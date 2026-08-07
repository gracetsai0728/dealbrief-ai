from agents import RunContextWrapper, function_tool
from sqlalchemy import or_

from ..extensions import db
from ..models import Customer, IntelligenceSnapshot, Product, Subscription
from .context import (
    CustomerProfileContext,
    CustomerRunContext,
    IntelligenceRunContext,
    LatestIntelligenceContext,
    LatestSubscriptionContext,
    MeetingBriefRunContext,
    ProductContext,
    SubscriptionContext,
)


def _iso(value):
    return value.isoformat() if value else None


def _customer_or_raise(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer or customer.deleted_at is not None:
        raise LookupError("The authorized customer no longer exists.")
    return customer


@function_tool(failure_error_function=None)
def get_customer_profile(
    context: RunContextWrapper[CustomerRunContext],
) -> CustomerProfileContext:
    """Return the authorized customer's name, industry, and account status."""
    customer = _customer_or_raise(context.context.customer_id)
    return CustomerProfileContext(
        id=str(customer.id),
        name=customer.name,
        industry=customer.industry,
        status=customer.status,
    )


@function_tool(failure_error_function=None)
def get_product_subscriptions(
    context: RunContextWrapper[IntelligenceRunContext],
) -> list[SubscriptionContext]:
    """Return subscriptions overlapping the authorized intelligence analysis period."""
    _customer_or_raise(context.context.customer_id)
    subscriptions = (
        Subscription.query.filter(
            Subscription.customer_id == context.context.customer_id,
            Subscription.subscription_start_date <= context.context.period_end,
            or_(
                Subscription.subscription_end_date.is_(None),
                Subscription.subscription_end_date >= context.context.period_start,
            ),
        )
        .order_by(Subscription.subscription_start_date.asc())
        .all()
    )
    return [
        SubscriptionContext(
            id=str(item.id),
            productId=str(item.product_id),
            product=item.product.name,
            subscriptionStartDate=_iso(item.subscription_start_date),
            subscriptionEndDate=_iso(item.subscription_end_date),
            subscriptionStatus=item.subscription_status,
            licensedSeats=item.licensed_seats,
        )
        for item in subscriptions
    ]


@function_tool(failure_error_function=None)
def get_product_context(
    context: RunContextWrapper[MeetingBriefRunContext],
) -> ProductContext:
    """Return the authorized product's name, description, and status."""
    product = db.session.get(Product, context.context.product_id)
    if not product or product.status != "active":
        raise LookupError("The authorized product no longer exists or is inactive.")
    return ProductContext(
        id=str(product.id),
        name=product.name,
        description=product.description,
        status=product.status,
    )


@function_tool(failure_error_function=None)
def get_latest_subscription(
    context: RunContextWrapper[MeetingBriefRunContext],
) -> LatestSubscriptionContext:
    """Return the latest subscription for the authorized customer and product."""
    _customer_or_raise(context.context.customer_id)
    subscription = (
        Subscription.query.filter_by(
            customer_id=context.context.customer_id,
            product_id=context.context.product_id,
        )
        .order_by(Subscription.subscription_start_date.desc())
        .first()
    )
    if not subscription:
        return LatestSubscriptionContext(found=False, subscription=None)
    return LatestSubscriptionContext(
        found=True,
        subscription=SubscriptionContext(
            id=str(subscription.id),
            productId=str(subscription.product_id),
            product=subscription.product.name,
            subscriptionStartDate=_iso(subscription.subscription_start_date),
            subscriptionEndDate=_iso(subscription.subscription_end_date),
            subscriptionStatus=subscription.subscription_status,
            licensedSeats=subscription.licensed_seats,
        ),
    )


@function_tool(failure_error_function=None)
def get_latest_intelligence(
    context: RunContextWrapper[MeetingBriefRunContext],
) -> LatestIntelligenceContext:
    """Return the latest saved intelligence snapshot for the authorized customer."""
    _customer_or_raise(context.context.customer_id)
    snapshot = (
        IntelligenceSnapshot.query.filter_by(
            customer_id=context.context.customer_id
        )
        .order_by(IntelligenceSnapshot.generated_at.desc())
        .first()
    )
    if not snapshot:
        return LatestIntelligenceContext(
            found=False,
            generatedAt=None,
            aiKeySignal=None,
            industryDynamics=[],
            companyNews=[],
            recommendedNextSteps=None,
            metrics=None,
        )
    return LatestIntelligenceContext(
        found=True,
        generatedAt=_iso(snapshot.generated_at),
        aiKeySignal=snapshot.ai_key_signal,
        industryDynamics=snapshot.industry_dynamics or [],
        companyNews=snapshot.company_news or [],
        recommendedNextSteps=snapshot.recommended_next_steps or None,
        metrics=snapshot.metrics or None,
    )
