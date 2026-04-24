import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from flask import Blueprint, current_app, g, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required
from sqlalchemy import func

from models import AssociationRule, Product, Transaction, TransactionItem
from rule_cache import hydrate_analyzer_from_db


admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

IMAGE_DIR = Path(__file__).resolve().parent.parent / "static" / "product_images"


def local_product_image_path(sku: str):
    for candidate in IMAGE_DIR.glob(f"{sku}.*"):
        if candidate.is_file():
            return candidate.name
    return None


def admin_required(fn):
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify({"error": "admin access required"}), 403
        return fn(*args, **kwargs)

    wrapper.__name__ = fn.__name__
    return wrapper


def product_dict(product: Product):
    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "category": product.category,
        "price": float(product.price),
        "description": product.description,
        "image_url": product.image_url,
    }


@admin_bp.post("/upload")
@admin_required
def upload_csv():
    if "file" not in request.files:
        return jsonify({"error": "csv file is required under form field 'file'"}), 400

    file = request.files["file"]
    if not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "only csv files are supported"}), 400

    frame = pd.read_csv(file)
    required_columns = {"session_id", "item_id", "item_name", "category", "price", "qty"}
    if not required_columns.issubset(set(frame.columns)):
        return jsonify({"error": f"csv must contain columns: {sorted(list(required_columns))}"}), 400

    # Replace prior transactional dataset with latest upload.
    g.db.query(TransactionItem).delete()
    g.db.query(Transaction).delete()
    g.db.commit()

    existing_products = {p.sku: p for p in g.db.query(Product).all()}

    for _, row in frame.drop_duplicates(subset=["item_id"]).iterrows():
        sku = str(row["item_id"]).strip()
        name = str(row["item_name"]).strip()
        category = str(row["category"]).strip()
        price = float(row["price"])

        if sku in existing_products:
            product = existing_products[sku]
            product.name = name
            product.category = category
            product.price = price
        else:
            local_image_name = local_product_image_path(sku)
            product = Product(
                sku=sku,
                name=name,
                category=category,
                price=price,
                description=f"{name} from {category}",
                image_url=(
                    f"/media/products/{local_image_name}"
                    if local_image_name
                    else f"https://placehold.co/400x300?text={sku}"
                ),
            )
            g.db.add(product)
            existing_products[sku] = product

    g.db.commit()

    grouped_sessions = frame.groupby("session_id")
    transactions_created = 0
    items_created = 0

    for session_id, session_rows in grouped_sessions:
        tx = Transaction(session_id=str(session_id), created_at=datetime.utcnow())
        g.db.add(tx)
        g.db.flush()

        grouped_items = session_rows.groupby("item_id", as_index=False).agg({"qty": "sum"})
        for _, item_row in grouped_items.iterrows():
            sku = str(item_row["item_id"]).strip()
            qty = int(item_row["qty"])
            product = existing_products.get(sku)
            if not product:
                continue

            tx_item = TransactionItem(transaction_id=tx.id, product_id=product.id, qty=max(1, qty))
            g.db.add(tx_item)
            items_created += 1

        transactions_created += 1

    g.db.commit()

    return jsonify(
        {
            "message": "upload processed",
            "transactions_created": transactions_created,
            "items_created": items_created,
            "products_total": g.db.query(Product).count(),
        }
    )


@admin_bp.post("/train")
@admin_required
def train_rules():
    analyzer = current_app.extensions["basket_analyzer"]

    payload = request.get_json(silent=True) or {}
    min_support = float(payload.get("min_support", analyzer.min_support))
    min_confidence = float(payload.get("min_confidence", analyzer.min_confidence))

    analyzer.min_support = min_support
    analyzer.min_confidence = min_confidence

    rows = (
        g.db.query(Transaction.session_id, Product.sku, TransactionItem.qty)
        .join(TransactionItem, Transaction.id == TransactionItem.transaction_id)
        .join(Product, Product.id == TransactionItem.product_id)
        .all()
    )

    raw_data = [{"session_id": str(r[0]), "item_id": r[1], "qty": int(r[2])} for r in rows]
    analyzer.ingest_batch_data(raw_data)
    analyzer.execute_mining_pipeline()

    g.db.query(AssociationRule).delete()
    g.db.commit()

    rules_generated = 0
    if not analyzer.association_rules_df.empty:
        for _, row in analyzer.association_rules_df.iterrows():
            db_rule = AssociationRule(
                antecedents=json.dumps(sorted(list(row["antecedents"]))),
                consequents=json.dumps(sorted(list(row["consequents"]))),
                support=float(row["support"]),
                confidence=float(row["confidence"]),
                lift=float(row["lift"]),
                is_active=True,
            )
            g.db.add(db_rule)
            rules_generated += 1

        g.db.commit()

    hydrate_analyzer_from_db(g.db, analyzer, active_only=True)

    return jsonify(
        {
            "message": "training completed",
            "rules_generated": rules_generated,
            "min_support": min_support,
            "min_confidence": min_confidence,
            "last_updated": analyzer.last_updated.isoformat() if analyzer.last_updated else None,
        }
    )


@admin_bp.get("/rules")
@admin_required
def list_rules():
    rules = g.db.query(AssociationRule).order_by(AssociationRule.lift.desc()).all()
    return jsonify(
        [
            {
                "id": r.id,
                "antecedents": json.loads(r.antecedents),
                "consequents": json.loads(r.consequents),
                "support": r.support,
                "confidence": r.confidence,
                "lift": r.lift,
                "created_at": r.created_at.isoformat(),
                "is_active": r.is_active,
            }
            for r in rules
        ]
    )


@admin_bp.patch("/rules/<int:rule_id>")
@admin_required
def toggle_rule(rule_id):
    payload = request.get_json(silent=True) or {}
    rule = g.db.query(AssociationRule).filter(AssociationRule.id == rule_id).first()
    if not rule:
        return jsonify({"error": "rule not found"}), 404

    if "is_active" in payload:
        rule.is_active = bool(payload["is_active"])
    else:
        rule.is_active = not rule.is_active

    g.db.commit()

    analyzer = current_app.extensions["basket_analyzer"]
    hydrate_analyzer_from_db(g.db, analyzer, active_only=True)

    return jsonify({"id": rule.id, "is_active": rule.is_active})


@admin_bp.get("/stats")
@admin_required
def stats():
    analyzer = current_app.extensions["basket_analyzer"]

    total_transactions = g.db.query(func.count(Transaction.id)).scalar() or 0
    total_rules = g.db.query(func.count(AssociationRule.id)).scalar() or 0

    top_rules = (
        g.db.query(AssociationRule)
        .filter(AssociationRule.is_active.is_(True))
        .order_by(AssociationRule.lift.desc())
        .limit(5)
        .all()
    )

    product_freq_rows = (
        g.db.query(Product.sku, Product.name, func.sum(TransactionItem.qty).label("frequency"))
        .join(TransactionItem, Product.id == TransactionItem.product_id)
        .group_by(Product.sku, Product.name)
        .order_by(func.sum(TransactionItem.qty).desc())
        .all()
    )

    product_frequencies = [
        {"sku": row[0], "name": row[1], "frequency": int(row[2]) if row[2] is not None else 0}
        for row in product_freq_rows
    ]

    top_product = product_frequencies[0] if product_frequencies else None

    last_rule = (
        g.db.query(AssociationRule.created_at)
        .order_by(AssociationRule.created_at.desc())
        .limit(1)
        .scalar()
    )

    return jsonify(
        {
            "total_transactions": int(total_transactions),
            "total_rules": int(total_rules),
            "top_product": top_product,
            "last_training_time": (
                analyzer.last_updated.isoformat()
                if analyzer.last_updated
                else (last_rule.isoformat() if last_rule else None)
            ),
            "top_rules": [
                {
                    "id": r.id,
                    "antecedents": json.loads(r.antecedents),
                    "consequents": json.loads(r.consequents),
                    "support": r.support,
                    "confidence": r.confidence,
                    "lift": r.lift,
                }
                for r in top_rules
            ],
            "product_frequencies": product_frequencies,
        }
    )
