def iso(value):
    return value.isoformat() if value else None


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
        "companyNews": snapshot.company_news or [],
        "recommendedNextSteps": {
            "crossSell": next_steps.get("crossSell", []),
            "upsell": next_steps.get("upsell", []),
            "renewal": next_steps.get("renewal", []),
            "winback": next_steps.get("winback", []),
        },
        "metrics": snapshot.metrics,
        "generatedAt": iso(snapshot.generated_at),
    }
