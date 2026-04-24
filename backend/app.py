from pathlib import Path
from datetime import timedelta

from flask import Flask, g, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from database import SessionLocal, init_db
from fp_growth_engine import EcommerceBasketAnalyzer
from rule_cache import hydrate_analyzer_from_db
from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.products import products_bp
from routes.recommendations import recommendations_bp


def create_app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=Config.JWT_ACCESS_TOKEN_EXPIRES_HOURS)
    app.config["JSON_SORT_KEYS"] = False

    CORS(app, resources={r"/*": {"origins": Config.CORS_ORIGINS}})
    JWTManager(app)

    init_db()

    analyzer = EcommerceBasketAnalyzer(
        min_support=Config.DEFAULT_MIN_SUPPORT,
        min_confidence=Config.DEFAULT_MIN_CONFIDENCE,
    )

    db = SessionLocal()
    try:
        hydrate_analyzer_from_db(db, analyzer, active_only=True)
    finally:
        db.close()

    app.extensions["basket_analyzer"] = analyzer

    @app.before_request
    def open_session():
        g.db = SessionLocal()

    @app.teardown_request
    def close_session(exception=None):
        db_session = getattr(g, "db", None)
        if not db_session:
            return
        if exception:
            db_session.rollback()
        db_session.close()
        SessionLocal.remove()

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    media_dir = Path(__file__).resolve().parent / "static" / "product_images"

    @app.get("/media/products/<path:filename>")
    def serve_product_image(filename):
        return send_from_directory(media_dir, filename)

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(recommendations_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
