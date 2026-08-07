from datetime import date, datetime, timezone
from uuid import UUID

from flask import Blueprint, g, jsonify, request, session
from sqlalchemy import text

from .auth import (
    admin_required,
    authenticate_user,
    load_current_user,
    register_user,
    serialize_user,
)
from .errors import ApiError
from .extensions import db
from .models import (
    Customer,
    IntelligenceSnapshot,
    Product,
    Subscription,
)
from .serializers import (
    serialize_customer,
    serialize_intelligence,
    serialize_product,
    serialize_subscription,
)
from .services.brief_service import find_customer, generate_brief
from .services.intelligence_service import refresh_intelligence


api = Blueprint("api", __name__)


@api.before_request
def require_authentication():
    # Browser CORS preflight requests do not carry the user's session cookie.
    # Let Flask-CORS answer OPTIONS; authentication still applies to the
    # subsequent API request.
    if request.method == "OPTIONS":
        return None
    load_current_user()
    if request.endpoint in {
        "api.health",
        "api.login",
        "api.register",
    }:
        return None
    if not g.current_user:
        raise ApiError("AUTHENTICATION_REQUIRED", "Please sign in to continue.", 401)
    return None


def parse_uuid(value, field_name="id"):
    try:
        return UUID(str(value))
    except (TypeError, ValueError) as error:
        raise ApiError("VALIDATION_ERROR", f"{field_name} must be a valid UUID.", 422) from error


def json_payload():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ApiError("VALIDATION_ERROR", "A JSON request body is required.", 422)
    return payload


def parse_date(value, field_name):
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError) as error:
        raise ApiError("VALIDATION_ERROR", f"{field_name} must use YYYY-MM-DD.", 422) from error


@api.get("/health")
def health():
    db.session.execute(text("SELECT 1"))
    return jsonify({"data": {"status": "ok"}})


@api.post("/auth/register")
def register():
    payload = json_payload()
    user = register_user(payload.get("name"), payload.get("email"), payload.get("password"))
    session.clear()
    session["user_id"] = str(user.id)
    return jsonify({"data": {"user": serialize_user(user)}}), 201


@api.post("/auth/login")
def login():
    payload = json_payload()
    user = authenticate_user(payload.get("email"), payload.get("password"))
    session.clear()
    session["user_id"] = str(user.id)
    return jsonify({"data": {"user": serialize_user(user)}})


@api.post("/auth/logout")
def logout():
    session.clear()
    return jsonify({"data": {"signedOut": True}})


@api.get("/auth/me")
def current_user():
    return jsonify({"data": {"user": serialize_user(g.current_user)}})


@api.get("/customers")
def list_customers():
    query = Customer.query.filter(Customer.deleted_at.is_(None))
    status = request.args.get("status")
    search = request.args.get("search")
    if status:
        query = query.filter_by(status=status.lower())
    if search:
        query = query.filter(Customer.name.ilike(f"%{search.strip()}%"))
    customers = query.order_by(Customer.name).all()
    return jsonify({"data": [serialize_customer(customer) for customer in customers]})


@api.post("/customers")
@admin_required
def create_customer():
    payload = json_payload()
    name = str(payload.get("name") or "").strip()
    if not name or len(name) > 200:
        raise ApiError("VALIDATION_ERROR", "Customer name is required.", 422)
    customer = Customer(
        name=name,
        industry=str(payload.get("industry") or "").strip() or None,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.session.add(customer)
    db.session.commit()
    return jsonify({"data": serialize_customer(customer)}), 201


@api.get("/products")
def list_products():
    products = Product.query.filter_by(status="active").order_by(Product.name).all()
    return jsonify({"data": [serialize_product(product) for product in products]})


@api.post("/products")
@admin_required
def create_product():
    payload = json_payload()
    name = str(payload.get("name") or "").strip()
    if not name or len(name) > 150:
        raise ApiError("VALIDATION_ERROR", "Product name is required.", 422)
    if Product.query.filter(db.func.lower(Product.name) == name.lower()).first():
        raise ApiError("PRODUCT_ALREADY_EXISTS", "A product with this name already exists.", 409)
    product = Product(
        name=name,
        description=str(payload.get("description") or "").strip() or None,
        status="active",
    )
    db.session.add(product)
    db.session.commit()
    return jsonify({"data": serialize_product(product)}), 201


@api.get("/subscriptions")
def list_subscriptions():
    query = Subscription.query.join(Customer).filter(Customer.deleted_at.is_(None))
    customer_id = request.args.get("customerId")
    if customer_id:
        query = query.filter(
            Subscription.customer_id == parse_uuid(customer_id, "customerId")
        )
    rows = query.order_by(Subscription.subscription_start_date.desc()).limit(500).all()
    return jsonify({"data": [serialize_subscription(item) for item in rows]})


@api.post("/subscriptions")
@admin_required
def create_subscription():
    payload = json_payload()
    customer_id = parse_uuid(payload.get("customerId"), "customerId")
    product_id = parse_uuid(payload.get("productId"), "productId")
    customer = db.session.get(Customer, customer_id)
    product = db.session.get(Product, product_id)
    if not customer or customer.deleted_at is not None:
        raise ApiError("CUSTOMER_NOT_FOUND", "The requested customer does not exist.", 404)
    if not product or product.status != "active":
        raise ApiError("PRODUCT_NOT_FOUND", "The requested product does not exist.", 404)
    try:
        licensed_seats = int(payload["licensedSeats"]) if payload.get("licensedSeats") not in {None, ""} else None
    except (TypeError, ValueError) as error:
        raise ApiError("VALIDATION_ERROR", "Licensed seats must be a valid number.", 422) from error
    if licensed_seats is not None and licensed_seats < 0:
        raise ApiError("VALIDATION_ERROR", "Licensed seats cannot be negative.", 422)
    subscription_start_date = parse_date(
        payload.get("subscriptionStartDate"), "subscriptionStartDate"
    )
    subscription_end_date = (
        parse_date(payload["subscriptionEndDate"], "subscriptionEndDate")
        if payload.get("subscriptionEndDate")
        else None
    )
    if subscription_end_date and subscription_end_date < subscription_start_date:
        raise ApiError(
            "VALIDATION_ERROR",
            "subscriptionEndDate cannot be earlier than subscriptionStartDate.",
            422,
        )
    subscription_status = str(payload.get("subscriptionStatus") or "active").lower()
    if subscription_status not in {"active", "expired", "canceled"}:
        raise ApiError(
            "VALIDATION_ERROR",
            "subscriptionStatus must be active, expired, or canceled.",
            422,
        )
    existing = Subscription.query.filter_by(
        customer_id=customer_id,
        product_id=product_id,
        subscription_start_date=subscription_start_date,
    ).first()
    if existing:
        raise ApiError(
            "SUBSCRIPTION_ALREADY_EXISTS",
            "This customer already has the same product subscription start date.",
            409,
        )
    subscription = Subscription(
        customer_id=customer_id,
        product_id=product_id,
        subscription_start_date=subscription_start_date,
        subscription_end_date=subscription_end_date,
        subscription_status=subscription_status,
        licensed_seats=licensed_seats,
    )
    db.session.add(subscription)
    db.session.commit()
    return jsonify({"data": serialize_subscription(subscription)}), 201


@api.get("/customers/<customer_id>/timeline")
def customer_timeline(customer_id):
    customer = find_customer(customer_id)
    subscriptions = (
        Subscription.query.filter_by(customer_id=customer.id)
        .order_by(Subscription.subscription_start_date.asc())
        .all()
    )
    today = date.today()
    series_by_product = {}
    for subscription in subscriptions:
        chart_end = (
            min(subscription.subscription_end_date, today)
            if subscription.subscription_end_date
            else today
        )
        chart_end = max(chart_end, subscription.subscription_start_date)
        seat_points = []
        if subscription.licensed_seats is not None:
            seat_points.append(
                {
                    "date": subscription.subscription_start_date.isoformat(),
                    "seats": subscription.licensed_seats,
                }
            )
        product_key = str(subscription.product_id)
        product_series = series_by_product.setdefault(
            product_key,
            {
                "subscriptionId": str(subscription.id),
                "productId": product_key,
                "productName": subscription.product.name,
                "startDate": subscription.subscription_start_date.isoformat(),
                "endDate": subscription.subscription_end_date.isoformat()
                if subscription.subscription_end_date
                else None,
                "status": subscription.subscription_status,
                "licensedSeats": subscription.licensed_seats,
                "seatPoints": [],
                "_chartEnd": chart_end.isoformat(),
            },
        )
        product_series["subscriptionId"] = str(subscription.id)
        product_series["endDate"] = (
            subscription.subscription_end_date.isoformat()
            if subscription.subscription_end_date
            else None
        )
        product_series["status"] = subscription.subscription_status
        product_series["licensedSeats"] = subscription.licensed_seats
        product_series["_chartEnd"] = chart_end.isoformat()
        product_series["seatPoints"].extend(seat_points)
    series = list(series_by_product.values())
    for item in series:
        if (
            item["licensedSeats"] is not None
            and item["seatPoints"]
            and item["_chartEnd"] != item["seatPoints"][-1]["date"]
        ):
            item["seatPoints"].append(
                {
                    "date": item["_chartEnd"],
                    "seats": item["licensedSeats"],
                }
            )
        item.pop("_chartEnd")
    dates = [
        date.fromisoformat(point["date"])
        for item in series
        for point in item["seatPoints"]
    ]
    return jsonify(
        {
            "data": {
                "customer": serialize_customer(customer),
                "periodStart": min(
                    (
                        subscription.subscription_start_date
                        for subscription in subscriptions
                    ),
                    default=None,
                ).isoformat()
                if subscriptions
                else None,
                "periodEnd": max(dates).isoformat() if dates else None,
                "series": series,
            }
        }
    )


@api.get("/customers/<customer_id>/dashboard")
def customer_dashboard(customer_id):
    customer = find_customer(customer_id)
    subscriptions = (
        Subscription.query.filter_by(customer_id=customer.id)
        .order_by(Subscription.subscription_start_date.desc())
        .all()
    )
    latest_by_product = {}
    for subscription in subscriptions:
        latest_by_product.setdefault(subscription.product_id, subscription)

    intelligence = (
        IntelligenceSnapshot.query.filter_by(customer_id=customer.id)
        .order_by(IntelligenceSnapshot.generated_at.desc())
        .first()
    )
    return jsonify(
        {
            "data": {
                "customer": serialize_customer(customer),
                "latestSubscriptions": [
                    serialize_subscription(item) for item in latest_by_product.values()
                ],
                "intelligence": serialize_intelligence(intelligence),
            }
        }
    )


@api.delete("/customers/<customer_id>")
@admin_required
def delete_customer(customer_id):
    customer = find_customer(customer_id)
    customer.deleted_at = datetime.now(timezone.utc)
    customer.status = "inactive"
    customer.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(
        {
            "data": {
                "id": str(customer.id),
                "deleted": True,
                "deleteMode": "soft",
                "deletedAt": customer.deleted_at.isoformat(),
            }
        }
    )


@api.delete("/subscriptions/<subscription_id>")
@admin_required
def delete_subscription(subscription_id):
    subscription = db.session.get(
        Subscription, parse_uuid(subscription_id, "subscriptionId")
    )
    if not subscription:
        raise ApiError(
            "SUBSCRIPTION_NOT_FOUND",
            "The requested subscription does not exist.",
            404,
        )
    deleted_id = str(subscription.id)
    db.session.delete(subscription)
    db.session.commit()
    return jsonify(
        {"data": {"id": deleted_id, "deleted": True, "deleteMode": "hard"}}
    )


@api.post("/generate-brief")
def create_brief():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ApiError("VALIDATION_ERROR", "A JSON request body is required.", 422)
    return jsonify({"data": generate_brief(payload)}), 201


@api.get("/customers/<customer_id>/intelligence")
def list_intelligence(customer_id):
    customer = find_customer(customer_id)
    snapshots = (
        IntelligenceSnapshot.query.filter_by(customer_id=customer.id)
        .order_by(IntelligenceSnapshot.generated_at.desc())
        .limit(50)
        .all()
    )
    return jsonify({"data": [serialize_intelligence(item) for item in snapshots]})


@api.get("/customers/<customer_id>/intelligence/latest")
def latest_intelligence(customer_id):
    customer = find_customer(customer_id)
    snapshot = (
        IntelligenceSnapshot.query.filter_by(customer_id=customer.id)
        .order_by(IntelligenceSnapshot.generated_at.desc())
        .first()
    )
    if not snapshot:
        raise ApiError(
            "INTELLIGENCE_NOT_FOUND",
            "No intelligence snapshot exists for this customer.",
            404,
        )
    return jsonify({"data": serialize_intelligence(snapshot)})


@api.post("/customers/<customer_id>/intelligence/refresh")
def create_intelligence(customer_id):
    payload = request.get_json(silent=True)
    snapshot = refresh_intelligence(customer_id, payload)
    return jsonify({"data": serialize_intelligence(snapshot)}), 201
