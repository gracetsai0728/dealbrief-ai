from datetime import date, datetime, time, timedelta, timezone
from uuid import uuid4

from flask import current_app
from sqlalchemy import or_

from ..errors import ApiError
from ..extensions import db
from ..models import IntelligenceSnapshot, Subscription
from .brief_service import find_customer
from .company_news_service import normalize_news_mode, resolve_company_news
from .openai_service import generate_structured_intelligence
from .recommendation_priority import (
    apply_recommendation_priorities,
    load_priority_decisions,
    serialize_priority_guidance,
)


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
    subscription_exists = (
        Subscription.query.filter(
            Subscription.customer_id == customer.id,
            Subscription.subscription_start_date <= period_end.date(),
            or_(
                Subscription.subscription_end_date.is_(None),
                Subscription.subscription_end_date >= period_start.date(),
            ),
        )
        .with_entities(Subscription.id)
        .first()
        is not None
    )

    return {
        "customerId": str(customer.id),
        "analysisPeriod": {
            "start": _iso(period_start),
            "end": _iso(period_end),
        },
        "hasSubscriptions": subscription_exists,
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
    if not context["hasSubscriptions"]:
        raise ApiError(
            "INSUFFICIENT_SOURCE_DATA",
            "At least one product subscription is required.",
            409,
        )

    priority_decisions = load_priority_decisions(customer.id, period_end.date())
    context["priorityGuidance"] = serialize_priority_guidance(priority_decisions)
    context["newsMode"] = normalize_news_mode(
        current_app.config.get("INTELLIGENCE_NEWS_MODE")
    )
    generated = generate_structured_intelligence(context)
    content = generated["content"]
    content["recommendedNextSteps"] = apply_recommendation_priorities(
        content["recommendedNextSteps"],
        priority_decisions,
    )
    subscriptions = (
        Subscription.query.filter_by(customer_id=customer.id)
        .order_by(Subscription.subscription_start_date.desc())
        .all()
    )
    content["companyNews"] = resolve_company_news(
        context["newsMode"],
        content.get("companyNews"),
        customer,
        subscriptions,
        period_end.date(),
    )
    generated_at = datetime.now(timezone.utc)

    snapshot = IntelligenceSnapshot(
        id=uuid4(),
        customer_id=customer.id,
        recommended_next_steps=content["recommendedNextSteps"],
        industry_dynamics=content["industryDynamics"],
        company_news=content["companyNews"],
        ai_key_signal=content["aiKeySignal"],
        metrics=content["metrics"],
        generated_at=generated_at,
    )
    db.session.add(snapshot)
    db.session.commit()
    return snapshot
