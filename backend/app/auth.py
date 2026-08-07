from functools import wraps
from uuid import UUID

from flask import g, session
from werkzeug.security import check_password_hash, generate_password_hash

from .errors import ApiError
from .extensions import db
from .models import User


def serialize_user(user):
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "role": user.role,
    }


def load_current_user():
    user_id = session.get("user_id")
    try:
        user_uuid = UUID(user_id) if user_id else None
    except (TypeError, ValueError):
        user_uuid = None
    user = db.session.get(User, user_uuid) if user_uuid else None
    g.current_user = user if user and user.is_active else None
    return g.current_user


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not getattr(g, "current_user", None):
            raise ApiError("AUTHENTICATION_REQUIRED", "Please sign in to continue.", 401)
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if g.current_user.role != "admin":
            raise ApiError("ADMIN_REQUIRED", "Administrator access is required.", 403)
        return view(*args, **kwargs)

    return wrapped


def register_user(name, email, password):
    name = str(name or "").strip()
    email = str(email or "").strip().lower()
    password = str(password or "")
    if not name or len(name) > 100:
        raise ApiError("VALIDATION_ERROR", "Name is required and must be 100 characters or fewer.", 422)
    if not email or "@" not in email or len(email) > 255:
        raise ApiError("VALIDATION_ERROR", "A valid email is required.", 422)
    if len(password) < 8:
        raise ApiError("VALIDATION_ERROR", "Password must be at least 8 characters.", 422)
    if User.query.filter_by(email=email).first():
        raise ApiError("EMAIL_ALREADY_REGISTERED", "An account with this email already exists.", 409)

    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        role="user",
        is_active=True,
    )
    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(email, password):
    email = str(email or "").strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user or not user.is_active or not check_password_hash(user.password_hash, str(password or "")):
        raise ApiError("INVALID_CREDENTIALS", "Email or password is incorrect.", 401)
    return user
