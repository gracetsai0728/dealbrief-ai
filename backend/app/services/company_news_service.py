from datetime import date, timedelta


VALID_NEWS_MODES = {"real", "hybrid", "mock"}
SYNTHETIC_SOURCE_NAME = "DealBrief Synthetic Scenario"


def normalize_news_mode(value):
    normalized = str(value or "hybrid").strip().lower()
    return normalized if normalized in VALID_NEWS_MODES else "hybrid"


def _active_subscriptions(subscriptions, as_of):
    return [
        subscription
        for subscription in subscriptions
        if subscription.subscription_start_date <= as_of
        and (
            subscription.subscription_end_date is None
            or subscription.subscription_end_date >= as_of
        )
        and subscription.subscription_status == "active"
    ]


def _industry_scenario(customer_name, industry):
    normalized = (industry or "").lower()
    scenarios = {
        "financial": (
            f"{customer_name} considers a simulated data-governance initiative",
            "a fictional program connecting analytics controls, audit workflows, and shared data standards",
        ),
        "retail": (
            f"{customer_name} explores a simulated connected-store initiative",
            "a fictional program linking store operations, inventory visibility, and regional planning",
        ),
        "health": (
            f"{customer_name} forms a simulated digital-workflow council",
            "a fictional council reviewing access controls, service workflows, and measurable adoption",
        ),
        "manufactur": (
            f"{customer_name} plans a simulated connected-operations program",
            "a fictional program joining operational reporting, capacity planning, and exception workflows",
        ),
        "education": (
            f"{customer_name} launches a simulated coordinated-services program",
            "a fictional program helping staff coordinate requests, follow-up actions, and outcome reporting",
        ),
    }
    for keyword, scenario in scenarios.items():
        if keyword in normalized:
            return scenario
    return (
        f"{customer_name} evaluates a simulated workflow-modernization initiative",
        "a fictional program connecting customer workflows, reporting, and cross-team coordination",
    )


def build_synthetic_company_news(customer, subscriptions, as_of):
    active = _active_subscriptions(subscriptions, as_of)
    selected = active or list(subscriptions)
    product_names = list(
        dict.fromkeys(
            subscription.product.name
            for subscription in selected
            if subscription.product is not None
        )
    )
    primary_product = product_names[0] if product_names else "core platform"
    total_seats = sum(subscription.licensed_seats or 0 for subscription in active)
    footprint = (
        f" across {total_seats:,} licensed seats"
        if total_seats
        else " across its current subscription footprint"
    )
    industry_headline, industry_detail = _industry_scenario(
        customer.name,
        customer.industry,
    )

    return [
        {
            "headline": (
                f"{customer.name} evaluates a simulated {primary_product} expansion"
            ),
            "summary": (
                "Synthetic demo scenario — not real company news. "
                f"This fictional update imagines {customer.name} extending "
                f"{primary_product}{footprint} to support additional teams."
            ),
            "sourceName": SYNTHETIC_SOURCE_NAME,
            "sourceUrl": None,
            "publishedDate": (as_of - timedelta(days=14)).isoformat(),
            "sourceType": "synthetic",
            "isMock": True,
        },
        {
            "headline": industry_headline,
            "summary": (
                "Synthetic demo scenario — not real company news. "
                f"This fictional update describes {industry_detail}."
            ),
            "sourceName": SYNTHETIC_SOURCE_NAME,
            "sourceUrl": None,
            "publishedDate": (as_of - timedelta(days=42)).isoformat(),
            "sourceType": "synthetic",
            "isMock": True,
        },
    ]


def _normalize_web_item(item):
    source_url = item.get("sourceUrl")
    if not source_url:
        return None
    return {
        "headline": item["headline"],
        "summary": item["summary"],
        "sourceName": item["sourceName"],
        "sourceUrl": source_url,
        "publishedDate": item.get("publishedDate"),
        "sourceType": "web",
        "isMock": False,
    }


def _normalize_synthetic_item(item):
    summary = item.get("summary", "").strip()
    if not summary.lower().startswith("synthetic demo scenario"):
        summary = f"Synthetic demo scenario — not real company news. {summary}"
    return {
        "headline": item["headline"],
        "summary": summary,
        "sourceName": SYNTHETIC_SOURCE_NAME,
        "sourceUrl": None,
        "publishedDate": item.get("publishedDate"),
        "sourceType": "synthetic",
        "isMock": True,
    }


def resolve_company_news(mode, generated_items, customer, subscriptions, as_of=None):
    news_mode = normalize_news_mode(mode)
    as_of = as_of or date.today()
    generated_items = generated_items or []

    web_items = [
        normalized
        for item in generated_items
        if item.get("sourceType") == "web" and not item.get("isMock")
        if (normalized := _normalize_web_item(item)) is not None
    ]
    synthetic_items = [
        _normalize_synthetic_item(item)
        for item in generated_items
        if item.get("sourceType") == "synthetic" or item.get("isMock")
    ]

    if news_mode == "real":
        return web_items[:5]
    if news_mode == "hybrid" and web_items:
        return web_items[:5]
    if synthetic_items:
        return synthetic_items[:2]
    return build_synthetic_company_news(customer, subscriptions, as_of)
