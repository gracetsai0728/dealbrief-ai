from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from ..errors import ApiError
from ..extensions import db
from ..models import Engagement, IntelligenceSnapshot, UsageSnapshot
from .brief_service import find_customer
from .openai_service import generate_structured_intelligence


def _number(value):
    return float(value) if isinstance(value, Decimal) else value


def _iso(value):
    return value.isoformat() if value else None


def _parse_boundary(value, field_name, end=False):
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed_date = date.fromisoformat(str(value))
        except ValueError as error:
            raise ApiError(
                "VALIDATION_ERROR",
                f"{field_name} must be an ISO 8601 date or timestamp.",
                422,
            ) from error
        parsed = datetime.combine(parsed_date, time.max if end else time.min)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def build_intelligence_context(customer, period_start, period_end):
    usage_rows = (
        UsageSnapshot.query.filter(
            UsageSnapshot.customer_id == customer.id,
            UsageSnapshot.snapshot_date >= period_start.date(),
            UsageSnapshot.snapshot_date <= period_end.date(),
        )
        .order_by(UsageSnapshot.snapshot_date.asc())
        .all()
    )
    engagements = (
        Engagement.query.filter(
            Engagement.customer_id == customer.id,
            Engagement.status == "saved",
            Engagement.occurred_at >= period_start,
            Engagement.occurred_at <= period_end,
        )
        .order_by(Engagement.occurred_at.asc())
        .all()
    )

    return {
        "analysisPeriod": {
            "start": _iso(period_start),
            "end": _iso(period_end),
        },
        "customer": {
            "id": str(customer.id),
            "name": customer.name,
            "industry": customer.industry,
            "opportunityStage": customer.opportunity_stage,
            "renewalDate": _iso(customer.renewal_date),
            "status": customer.status,
        },
        "usageSnapshots": [
            {
                "product": item.product.name,
                "snapshotDate": _iso(item.snapshot_date),
                "activeUsers": item.active_users,
                "licensedSeats": item.licensed_seats,
                "licenseUtilization": _number(item.license_utilization),
                "usageGrowth": _number(item.usage_growth),
                "featureAdoption": item.feature_adoption,
            }
            for item in usage_rows
        ],
        "savedEngagements": [
            {
                "occurredAt": _iso(item.occurred_at),
                "meetingType": item.meeting_type,
                "product": item.product.name if item.product else None,
                "title": item.title,
                "summary": item.summary,
                "notes": item.notes,
            }
            for item in engagements
        ],
    }


def refresh_intelligence(customer_reference, payload=None):
    payload = payload or {}
    if not isinstance(payload, dict):
        raise ApiError("VALIDATION_ERROR", "A JSON object is required.", 422)

    customer = find_customer(customer_reference)
    period_end = _parse_boundary(payload.get("periodEnd"), "periodEnd", end=True)
    period_end = period_end or datetime.now(timezone.utc)
    period_start = _parse_boundary(payload.get("periodStart"), "periodStart")
    period_start = period_start or (period_end - timedelta(days=90))
    if period_start >= period_end:
        raise ApiError(
            "VALIDATION_ERROR",
            "periodStart must be earlier than periodEnd.",
            422,
        )

    context = build_intelligence_context(customer, period_start, period_end)
    if not context["usageSnapshots"] and not context["savedEngagements"]:
        raise ApiError(
            "INSUFFICIENT_SOURCE_DATA",
            "At least one usage snapshot or saved engagement is required.",
            409,
        )

    generated = generate_structured_intelligence(context)
    content = generated["content"]
    generated_at = datetime.now(timezone.utc)
    latest_engagement = max(
        (
            datetime.fromisoformat(item["occurredAt"])
            for item in context["savedEngagements"]
            if item["occurredAt"]
        ),
        default=None,
    )
    source_dates = [
        datetime.combine(
            date.fromisoformat(item["snapshotDate"]),
            time.max,
            tzinfo=timezone.utc,
        )
        for item in context["usageSnapshots"]
    ]
    if latest_engagement:
        source_dates.append(latest_engagement)

    actions = content["nextBestActions"]
    snapshot = IntelligenceSnapshot(
        id=uuid4(),
        customer_id=customer.id,
        snapshot_date=generated_at.date(),
        renewal_risk=content["renewalRisk"],
        expansion_signal=content["expansionSignal"],
        next_best_action=actions[0]["action"] if actions else None,
        next_best_actions=actions,
        ai_key_signal=content["aiKeySignal"],
        last_interaction_at=latest_engagement,
        metrics=content["metrics"],
        period_start=period_start,
        period_end=period_end,
        source_data_through=max(source_dates) if source_dates else None,
        generation_status="completed",
        model=generated["model"],
        prompt_version="customer-intelligence-v1",
        generated_at=generated_at,
    )
    db.session.add(snapshot)
    db.session.commit()
    return snapshot
