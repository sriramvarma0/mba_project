from flask import Blueprint, g, jsonify

from models import Product


products_bp = Blueprint("products", __name__, url_prefix="/api/products")


def product_to_dict(product: Product):
    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "category": product.category,
        "price": float(product.price),
        "description": product.description,
        "image_url": product.image_url,
    }


@products_bp.get("")
def list_products():
    products = g.db.query(Product).order_by(Product.name.asc()).all()
    return jsonify([product_to_dict(p) for p in products])


@products_bp.get("/<string:sku>")
def get_product(sku):
    product = g.db.query(Product).filter(Product.sku == sku).first()
    if not product:
        return jsonify({"error": "product not found"}), 404
    return jsonify(product_to_dict(product))
