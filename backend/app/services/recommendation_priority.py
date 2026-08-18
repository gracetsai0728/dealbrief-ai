from dataclasses import dataclass
from datetime import date

from ..models import Product, Subscription


PRIORITY_CATEGORIES = ("crossSell", "upsell", "renewal", "winback")


@dataclass(frozen=True)
class PriorityDecision:
    priority: str
    score: int
    rationale: str


def _priority_from_score(score):
    if score >= 5:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


def _commercial_value_points(licensed_seats):
    if licensed_seats >= 1000:
        return 2
    if licensed_seats >= 250:
        return 1
    return 0


def _renewal_urgency_points(days_until_renewal):
    if days_until_renewal is None:
        return 0
    if days_until_renewal <= 120:
        return 2
    if days_until_renewal <= 270:
        return 1
    return 0


def _winback_urgency_points(days_since_lapse):
    if days_since_lapse is None:
        return 0
    if days_since_lapse <= 180:
        return 2
    if days_since_lapse <= 365:
        return 1
    return 0


def _is_currently_active(subscription, as_of):
    return (
        subscription.subscription_status == "active"
        and subscription.subscription_start_date <= as_of
        and (
            subscription.subscription_end_date is None
            or subscription.subscription_end_date >= as_of
        )
    )


def _decision(score, rationale, maximum=None):
    bounded_score = min(score, maximum) if maximum is not None else score
    return PriorityDecision(
        priority=_priority_from_score(bounded_score),
        score=bounded_score,
        rationale=rationale,
    )


def calculate_priority_decisions(products, subscriptions, as_of):
    """Calculate stable commercial priorities from product and subscription facts.

    Each eligible motion receives 0-2 points for signal strength, urgency, and
    commercial value. Scores 5-6 are high, 3-4 medium, and 0-2 low. Eligibility
    gates prevent recommendations such as winback when no product has lapsed.
    """
    active_products = {
        str(product.id): getattr(product, "name", str(product.id))
        for product in products
        if product.status == "active"
    }
    active_product_ids = set(active_products)
    history_by_product = {}
    for subscription in subscriptions:
        if subscription.subscription_start_date > as_of:
            continue
        history_by_product.setdefault(str(subscription.product_id), []).append(
            subscription
        )
    for history in history_by_product.values():
        history.sort(key=lambda item: item.subscription_start_date)

    latest_by_product = {
        product_id: history[-1]
        for product_id, history in history_by_product.items()
        if history
    }
    current_active = {
        product_id: subscription
        for product_id, subscription in latest_by_product.items()
        if _is_currently_active(subscription, as_of)
    }
    lapsed = {
        product_id: subscription
        for product_id, subscription in latest_by_product.items()
        if product_id not in current_active
        and (
            subscription.subscription_status in {"expired", "canceled"}
            or (
                subscription.subscription_end_date is not None
                and subscription.subscription_end_date < as_of
            )
        )
    }

    total_active_seats = sum(
        max(subscription.licensed_seats or 0, 0)
        for subscription in current_active.values()
    )
    active_value = _commercial_value_points(total_active_seats)
    dated_renewals = [
        subscription.subscription_end_date
        for subscription in current_active.values()
        if subscription.subscription_end_date is not None
    ]
    next_renewal = min(dated_renewals) if dated_renewals else None
    days_until_renewal = (next_renewal - as_of).days if next_renewal else None
    renewal_urgency = _renewal_urgency_points(days_until_renewal)

    never_subscribed_product_ids = active_product_ids - set(history_by_product)
    if never_subscribed_product_ids:
        cross_sell_score = 2 + renewal_urgency + active_value
        missing_products = ", ".join(
            sorted(active_products[product_id] for product_id in never_subscribed_product_ids)
        )
        renewal_timing = (
            f"the next renewal is in {days_until_renewal} days"
            if days_until_renewal is not None
            else "there is no dated renewal"
        )
        cross_sell = _decision(
            cross_sell_score,
            (
                f"Missing active product(s): {missing_products}; the current portfolio "
                f"has {total_active_seats} licensed seats and {renewal_timing}."
            ),
        )
    else:
        cross_sell = _decision(
            0,
            "No never-purchased active product is available for cross-sell.",
        )

    growing_product_count = 0
    for product_id, current in current_active.items():
        history = history_by_product[product_id]
        if len(history) < 2:
            continue
        previous = history[-2]
        if (
            current.licensed_seats is not None
            and previous.licensed_seats is not None
            and current.licensed_seats > previous.licensed_seats
        ):
            growing_product_count += 1

    if current_active:
        expansion_signal = 2 if growing_product_count else 1
        upsell_score = expansion_signal + renewal_urgency + active_value
        upsell = _decision(
            upsell_score,
            (
                f"{growing_product_count} active product(s) show seat growth, "
                f"with {total_active_seats} current licensed seats."
            ),
            # An account without observed seat growth cannot be high priority
            # solely because it is large or approaching renewal.
            maximum=None if growing_product_count else 4,
        )
    else:
        upsell = _decision(0, "No active subscription is eligible for upsell.")

    if current_active:
        renewal_signal = 2 if next_renewal else 1
        renewal_score = renewal_signal + renewal_urgency + active_value
        renewal_timing = (
            f"in {days_until_renewal} days"
            if days_until_renewal is not None
            else "not currently dated"
        )
        renewal = _decision(
            renewal_score,
            (
                f"The next renewal is {renewal_timing} across "
                f"{len(current_active)} active product(s) and "
                f"{total_active_seats} licensed seats."
            ),
        )
    else:
        renewal = _decision(0, "No active subscription is eligible for renewal.")

    if lapsed:
        latest_lapse_date = max(
            subscription.subscription_end_date
            or subscription.subscription_start_date
            for subscription in lapsed.values()
        )
        days_since_lapse = max((as_of - latest_lapse_date).days, 0)
        former_seats = max(
            max(subscription.licensed_seats or 0, 0)
            for subscription in lapsed.values()
        )
        winback_score = (
            2
            + _winback_urgency_points(days_since_lapse)
            + _commercial_value_points(former_seats)
        )
        winback = _decision(
            winback_score,
            (
                f"{len(lapsed)} product(s) are lapsed; the most recent lapse was "
                f"{days_since_lapse} days ago and the largest former contract had "
                f"{former_seats} seats."
            ),
        )
    else:
        winback = _decision(
            0,
            "No currently lapsed product is eligible for winback.",
        )

    return {
        "crossSell": cross_sell,
        "upsell": upsell,
        "renewal": renewal,
        "winback": winback,
    }


def load_priority_decisions(customer_id, as_of):
    products = Product.query.filter_by(status="active").all()
    subscriptions = (
        Subscription.query.filter_by(customer_id=customer_id)
        .order_by(Subscription.subscription_start_date.asc())
        .all()
    )
    return calculate_priority_decisions(products, subscriptions, as_of)


def serialize_priority_guidance(decisions):
    return {
        category: {
            "priority": decision.priority,
            "score": decision.score,
            "rationale": decision.rationale,
        }
        for category, decision in decisions.items()
    }


def apply_recommendation_priorities(recommendations, decisions):

    prioritized = {}
    for category in PRIORITY_CATEGORIES:
        decision = decisions[category]
        prioritized[category] = []
        for recommendation in recommendations.get(category, []):
            item = dict(recommendation)
            item["priority"] = decision.priority
            prioritized[category].append(item)
    return prioritized
