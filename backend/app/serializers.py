def iso(value):
    return value.isoformat() if value else None


def _serialize_company_news(items):
    normalized_items = []
    for item in items or []:
        normalized = dict(item)
        source_name = str(normalized.get("sourceName") or "")
        is_mock = (
            bool(normalized.get("isMock"))
            or "mock" in source_name.lower()
            or "synthetic" in source_name.lower()
        )
        normalized["sourceType"] = "synthetic" if is_mock else "web"
        normalized["isMock"] = is_mock
        if is_mock:
            normalized["sourceName"] = "DealBrief Synthetic Scenario"
            normalized["sourceUrl"] = None
            summary = str(normalized.get("summary") or "").strip()
            if not summary.lower().startswith("synthetic demo scenario"):
                normalized["summary"] = (
                    "Synthetic demo scenario — not real company news. " + summary
                )
        normalized_items.append(normalized)
    return normalized_items


def serialize_customer(customer):
    return {
        "id": str(customer.id),
        "name": customer.name,
        "industry": customer.industry,
        "status": customer.status,
    }


def serialize_product(product):
    return {
        "id": str(product.id),
        "name": product.name,
        "description": product.description,
        "status": product.status,
    }


def serialize_subscription(subscription):
    return {
        "id": str(subscription.id),
        "customerId": str(subscription.customer_id),
        "customerName": subscription.customer.name if subscription.customer else None,
        "productId": str(subscription.product_id),
        "productName": subscription.product.name,
        "subscriptionStartDate": iso(subscription.subscription_start_date),
        "subscriptionEndDate": iso(subscription.subscription_end_date),
        "subscriptionStatus": subscription.subscription_status,
        "licensedSeats": subscription.licensed_seats,
    }


def serialize_intelligence(snapshot):
    if not snapshot:
        return None
    next_steps = snapshot.recommended_next_steps or {}
    return {
        "id": str(snapshot.id),
        "aiKeySignal": snapshot.ai_key_signal,
        "industryDynamics": snapshot.industry_dynamics or [],
        "companyNews": _serialize_company_news(snapshot.company_news),
        "recommendedNextSteps": {
            "crossSell": next_steps.get("crossSell", []),
            "upsell": next_steps.get("upsell", []),
            "renewal": next_steps.get("renewal", []),
            "winback": next_steps.get("winback", []),
        },
        "metrics": snapshot.metrics,
        "generatedAt": iso(snapshot.generated_at),
    }
