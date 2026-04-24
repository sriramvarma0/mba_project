from flask import Blueprint, current_app, g, jsonify, request

from models import Product
from rule_cache import hydrate_analyzer_from_db


recommendations_bp = Blueprint("recommendations", __name__)


@recommendations_bp.post("/api/recommend")
def recommend():
    payload = request.get_json(silent=True) or {}
    cart_items = payload.get("cart_items") or []
    if not isinstance(cart_items, list):
        return jsonify({"error": "cart_items must be a list"}), 400

    analyzer = current_app.extensions["basket_analyzer"]

    if not analyzer.rule_cache:
        hydrate_analyzer_from_db(g.db, analyzer, active_only=True)

    recommendations = analyzer.get_realtime_recommendations(cart_items, top_n=3)

    output = []
    for rec in recommendations:
        product = g.db.query(Product).filter(Product.sku == rec["recommended_item"]).first()
        output.append(
            {
                "sku": rec["recommended_item"],
                "confidence": rec["confidence"],
                "lift": rec["lift"],
                "support": rec["support"],
                "product": {
                    "name": product.name if product else rec["recommended_item"],
                    "category": product.category if product else "",
                    "price": float(product.price) if product else None,
                    "image_url": product.image_url if product else None,
                },
            }
        )

    return jsonify({"recommendations": output})


@recommendations_bp.post("/api/discount")
def discount():
    payload = request.get_json(silent=True) or {}
    cart_items = payload.get("cart_items") or []
    if not isinstance(cart_items, list):
        return jsonify({"error": "cart_items must be a list"}), 400

    analyzer = current_app.extensions["basket_analyzer"]
    if not analyzer.rule_cache:
        hydrate_analyzer_from_db(g.db, analyzer, active_only=True)

    promo = analyzer.trigger_dynamic_discount(cart_items)
    return jsonify({"promo_code": promo})
