from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_

from ..errors import ApiError
from ..extensions import db
from ..models import Customer, Engagement, IntelligenceSnapshot, Product, UsageSnapshot
from .openai_service import generate_structured_brief


MEETING_TYPES = {"qbr", "renewal", "discovery", "upsell"}
DELIVERABLE_ALIASES = {
    "call": "call_brief",
    "call brief": "call_brief",
    "call_brief": "call_brief",
    "email": "email_draft",
    "email draft": "email_draft",
    "email_draft": "email_draft",
    "meeting agenda": "meeting_agenda",
    "meeting_agenda": "meeting_agenda",
}
DELIVERABLE_LABELS = {
    "call_brief": "Call Brief",
    "email_draft": "Email Draft",
    "meeting_agenda": "Meeting Agenda",
}


def _as_float(value):
    return float(value) if isinstance(value, Decimal) else value


def _iso(value):
    return value.isoformat() if value else None


def _uuid(value):
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def find_customer(reference):
    if not reference:
        raise ApiError("VALIDATION_ERROR", "customerId is required.", 422)

    customer_uuid = _uuid(reference)
    if customer_uuid:
        customer = db.session.get(Customer, customer_uuid)
    else:
        normalized = str(reference).strip().lower()
        customer = Customer.query.filter(
            or_(
                func.lower(Customer.name) == normalized,
                func.lower(func.replace(Customer.name, " ", "-")) == normalized,
                func.lower(Customer.salesforce_account_id) == normalized,
            )
        ).first()

    if not customer or customer.deleted_at is not None:
        raise ApiError("CUSTOMER_NOT_FOUND", "The requested customer does not exist.", 404)
    return customer


def find_product(reference):
    if not reference:
        raise ApiError("VALIDATION_ERROR", "productId or product is required.", 422)

    product_uuid = _uuid(reference)
    product = db.session.get(Product, product_uuid) if product_uuid else None
    if not product:
        product = Product.query.filter(func.lower(Product.name) == str(reference).strip().lower()).first()
    if not product or product.status != "active":
        raise ApiError("PRODUCT_NOT_FOUND", "The requested product does not exist or is inactive.", 404)
    return product


def normalize_generation_request(payload):
    meeting_type = str(payload.get("meetingType", "")).strip().lower()
    if meeting_type not in MEETING_TYPES:
        raise ApiError(
            "VALIDATION_ERROR",
            "meetingType must be one of: qbr, renewal, discovery, upsell.",
            422,
        )

    deliverable_value = payload.get("deliverableType") or payload.get("deliverable") or ""
    deliverable_type = DELIVERABLE_ALIASES.get(str(deliverable_value).strip().lower())
    if not deliverable_type:
        raise ApiError(
            "VALIDATION_ERROR",
            "deliverableType must be call_brief, email_draft, or meeting_agenda.",
            422,
        )

    notes = str(payload.get("notes", "")).strip()
    if len(notes) > 2000:
        raise ApiError("VALIDATION_ERROR", "notes must be 2000 characters or fewer.", 422)

    return meeting_type, deliverable_type, notes


def build_brief_context(customer, product, meeting_type, deliverable_type, notes):
    usage = (
        UsageSnapshot.query.filter_by(customer_id=customer.id, product_id=product.id)
        .order_by(UsageSnapshot.snapshot_date.desc())
        .first()
    )
    intelligence = (
        IntelligenceSnapshot.query.filter_by(customer_id=customer.id)
        .order_by(IntelligenceSnapshot.generated_at.desc())
        .first()
    )
    recent_engagements = (
        Engagement.query.filter_by(customer_id=customer.id, status="saved")
        .order_by(Engagement.generated_at.desc())
        .limit(5)
        .all()
    )

    return {
        "customer": {
            "id": str(customer.id),
            "name": customer.name,
            "industry": customer.industry,
            "opportunityStage": customer.opportunity_stage,
            "renewalDate": _iso(customer.renewal_date),
            "status": customer.status,
        },
        "product": {"id": str(product.id), "name": product.name},
        "latestUsage": None
        if not usage
        else {
            "snapshotDate": _iso(usage.snapshot_date),
            "activeUsers": usage.active_users,
            "licensedSeats": usage.licensed_seats,
            "licenseUtilization": _as_float(usage.license_utilization),
            "usageGrowth": _as_float(usage.usage_growth),
            "featureAdoption": usage.feature_adoption,
        },
        "latestIntelligence": None
        if not intelligence
        else {
            "snapshotDate": _iso(intelligence.snapshot_date),
            "nextBestActions": intelligence.next_best_actions or [],
            "aiKeySignal": intelligence.ai_key_signal,
            "metrics": intelligence.metrics,
        },
        "recentEngagements": [
            {
                "meetingType": item.meeting_type,
                "deliverableType": item.deliverable_type,
                "title": item.title,
                "summary": item.summary,
                "generatedAt": _iso(item.generated_at),
            }
            for item in recent_engagements
        ],
        "request": {
            "meetingType": meeting_type,
            "deliverableType": deliverable_type,
            "notes": notes or None,
        },
    }


def generate_brief(payload):
    customer = find_customer(payload.get("customerId") or payload.get("customer"))
    product = find_product(payload.get("productId") or payload.get("product"))
    meeting_type, deliverable_type, notes = normalize_generation_request(payload)
    context = build_brief_context(customer, product, meeting_type, deliverable_type, notes)
    generated = generate_structured_brief(context, deliverable_type)
    content = generated["content"]
    now = datetime.now(timezone.utc)

    engagement = Engagement(
        customer_id=customer.id,
        product_id=product.id,
        created_by=customer.account_owner_id,
        engagement_type="generated_brief",
        meeting_type=meeting_type,
        deliverable_type=deliverable_type,
        occurred_at=now,
        title=content["title"],
        summary=content["summary"],
        notes=notes or None,
        content=content,
        input_snapshot=context,
        model=generated["model"],
        prompt_version="meeting-brief-v1",
        generated_at=now,
        status="draft",
    )
    db.session.add(engagement)
    db.session.commit()

    response = {
        **content,
        "id": str(engagement.id),
        "engagementId": str(engagement.id),
        "customerId": str(customer.id),
        "customerName": customer.name,
        "productId": str(product.id),
        "product": product.name,
        "meetingType": meeting_type.upper() if meeting_type == "qbr" else meeting_type.title(),
        "deliverable": DELIVERABLE_LABELS[deliverable_type],
        "deliverableType": deliverable_type,
        "status": engagement.status,
        "generatedAt": _iso(engagement.generated_at),
    }
    return response
