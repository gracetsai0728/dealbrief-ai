from datetime import datetime, timezone
from uuid import UUID

from flask import Blueprint, jsonify, request
from sqlalchemy import text

from .errors import ApiError
from .extensions import db
from .models import (
    Customer,
    Engagement,
    ImportJob,
    IntelligenceSnapshot,
    Product,
    UsageSnapshot,
)
from .serializers import (
    serialize_customer,
    serialize_engagement,
    serialize_import_job,
    serialize_intelligence,
    serialize_usage,
)
from .services.brief_service import find_customer, generate_brief
from .services.import_service import import_customers, import_usage
from .services.intelligence_service import refresh_intelligence


api = Blueprint("api", __name__)


def parse_uuid(value, field_name="id"):
    try:
        return UUID(str(value))
    except (TypeError, ValueError) as error:
        raise ApiError("VALIDATION_ERROR", f"{field_name} must be a valid UUID.", 422) from error


@api.get("/health")
def health():
    db.session.execute(text("SELECT 1"))
    return jsonify({"data": {"status": "ok"}})


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


@api.get("/products")
def list_products():
    products = Product.query.filter_by(status="active").order_by(Product.name).all()
    return jsonify(
        {
            "data": [
                {
                    "id": str(product.id),
                    "name": product.name,
                    "description": product.description,
                    "status": product.status,
                }
                for product in products
            ]
        }
    )


@api.get("/usage")
def list_usage():
    query = UsageSnapshot.query
    customer_id = request.args.get("customerId")
    if customer_id:
        query = query.filter_by(customer_id=parse_uuid(customer_id, "customerId"))
    rows = query.order_by(UsageSnapshot.snapshot_date.desc()).limit(500).all()
    return jsonify({"data": [serialize_usage(item) for item in rows]})


@api.get("/customers/<customer_id>/dashboard")
def customer_dashboard(customer_id):
    customer = find_customer(customer_id)
    usage_rows = (
        UsageSnapshot.query.filter_by(customer_id=customer.id)
        .order_by(UsageSnapshot.snapshot_date.desc())
        .all()
    )
    latest_by_product = {}
    for usage in usage_rows:
        latest_by_product.setdefault(usage.product_id, usage)

    intelligence = (
        IntelligenceSnapshot.query.filter_by(customer_id=customer.id)
        .order_by(IntelligenceSnapshot.generated_at.desc())
        .first()
    )
    engagements = (
        Engagement.query.filter_by(customer_id=customer.id, status="saved")
        .order_by(Engagement.generated_at.desc())
        .limit(20)
        .all()
    )
    return jsonify(
        {
            "data": {
                "customer": serialize_customer(customer),
                "latestUsage": [serialize_usage(item) for item in latest_by_product.values()],
                "intelligence": serialize_intelligence(intelligence),
                "engagementTimeline": [serialize_engagement(item) for item in engagements],
            }
        }
    )


@api.delete("/customers/<customer_id>")
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


@api.delete("/usage/<usage_id>")
def delete_usage(usage_id):
    usage = db.session.get(UsageSnapshot, parse_uuid(usage_id, "usageId"))
    if not usage:
        raise ApiError("USAGE_NOT_FOUND", "The requested usage snapshot does not exist.", 404)
    deleted_id = str(usage.id)
    db.session.delete(usage)
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


@api.get("/engagement-log")
def list_engagements():
    query = Engagement.query.filter_by(status="saved")
    customer_id = request.args.get("customerId")
    if customer_id:
        query = query.filter_by(customer_id=parse_uuid(customer_id, "customerId"))
    engagements = query.order_by(Engagement.generated_at.desc()).limit(100).all()
    return jsonify({"data": [serialize_engagement(item) for item in engagements]})


@api.get("/engagement-log/<engagement_id>")
def get_engagement(engagement_id):
    engagement = db.session.get(Engagement, parse_uuid(engagement_id, "engagementId"))
    if not engagement:
        raise ApiError("ENGAGEMENT_NOT_FOUND", "The requested engagement does not exist.", 404)
    return jsonify({"data": serialize_engagement(engagement, include_content=True)})


@api.post("/engagement-log")
def save_engagement():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ApiError("VALIDATION_ERROR", "A JSON request body is required.", 422)
    engagement_id = payload.get("engagementId") or payload.get("id")
    engagement = db.session.get(Engagement, parse_uuid(engagement_id, "engagementId"))
    if not engagement:
        raise ApiError("ENGAGEMENT_NOT_FOUND", "The requested engagement does not exist.", 404)
    if engagement.status == "archived":
        raise ApiError("ENGAGEMENT_ARCHIVED", "An archived engagement cannot be saved.", 409)
    engagement.status = "saved"
    db.session.commit()
    return jsonify({"data": serialize_engagement(engagement, include_content=True)})


@api.patch("/engagement-log/<engagement_id>")
def update_engagement(engagement_id):
    payload = request.get_json(silent=True) or {}
    status = payload.get("status")
    if status not in {"draft", "saved", "archived"}:
        raise ApiError("VALIDATION_ERROR", "status must be draft, saved, or archived.", 422)
    engagement = db.session.get(Engagement, parse_uuid(engagement_id, "engagementId"))
    if not engagement:
        raise ApiError("ENGAGEMENT_NOT_FOUND", "The requested engagement does not exist.", 404)
    engagement.status = status
    db.session.commit()
    return jsonify({"data": serialize_engagement(engagement, include_content=True)})


@api.delete("/engagement-log/<engagement_id>")
def delete_engagement(engagement_id):
    engagement = db.session.get(Engagement, parse_uuid(engagement_id, "engagementId"))
    if not engagement:
        raise ApiError("ENGAGEMENT_NOT_FOUND", "The requested engagement does not exist.", 404)
    engagement.status = "archived"
    engagement.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(
        {
            "data": {
                "id": str(engagement.id),
                "deleted": True,
                "deleteMode": "archive",
                "status": engagement.status,
            }
        }
    )


@api.get("/imports")
def list_import_jobs():
    import_type = request.args.get("type")
    query = ImportJob.query
    if import_type:
        if import_type not in {"customers", "usage"}:
            raise ApiError(
                "VALIDATION_ERROR",
                "type must be customers or usage.",
                422,
            )
        query = query.filter_by(import_type=import_type)
    jobs = query.order_by(ImportJob.created_at.desc()).limit(100).all()
    return jsonify({"data": [serialize_import_job(job) for job in jobs]})


@api.get("/imports/<import_job_id>")
def get_import_job(import_job_id):
    job = db.session.get(ImportJob, parse_uuid(import_job_id, "importJobId"))
    if not job:
        raise ApiError("IMPORT_NOT_FOUND", "The requested import job does not exist.", 404)
    return jsonify({"data": serialize_import_job(job)})


@api.post("/imports/customers")
def create_customer_import():
    job = import_customers(request.get_json(silent=True))
    return jsonify({"data": serialize_import_job(job)}), 201


@api.post("/imports/usage")
def create_usage_import():
    job = import_usage(request.get_json(silent=True))
    return jsonify({"data": serialize_import_job(job)}), 201


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
