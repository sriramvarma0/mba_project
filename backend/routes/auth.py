from flask import Blueprint, g, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, get_jwt, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash

from models import User


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    role = (payload.get("role") or "customer").strip().lower()

    if role not in {"admin", "customer"}:
        return jsonify({"error": "role must be admin or customer"}), 400
    if not username or not email or not password:
        return jsonify({"error": "username, email, and password are required"}), 400

    existing = g.db.query(User).filter((User.email == email) | (User.username == username)).first()
    if existing:
        return jsonify({"error": "user with username/email already exists"}), 409

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        role=role,
    )
    g.db.add(user)
    g.db.commit()

    return jsonify({"message": "registration successful", "user_id": user.id}), 201


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    user = g.db.query(User).filter(User.email == email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "invalid credentials"}), 401

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify(
        {
            "access_token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
            },
        }
    )


@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    claims = get_jwt()
    user = g.db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    return jsonify(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": claims.get("role", user.role),
        }
    )
