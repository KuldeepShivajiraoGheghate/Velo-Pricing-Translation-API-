"""
Stripe Connector — syncs products/prices from Stripe into Velo Plan format.
"""
import stripe


def fetch_stripe_plans(api_key: str) -> list[dict]:
    """
    Fetch active products & prices from Stripe API and normalize into Velo Plan dicts.
    """
    if not api_key:
        raise ValueError("Stripe API key is required.")

    stripe.api_key = api_key

    prices = stripe.Price.list(active=True, limit=100, expand=["data.product"])
    plans = []

    for price in prices.data:
        # Resolve product name
        product_name = "Plan"
        if hasattr(price, "product") and price.product:
            if isinstance(price.product, str):
                product_name = price.product
            else:
                product_name = getattr(price.product, "name", None) or "Plan"

        interval = "month"
        if hasattr(price, "recurring") and price.recurring:
            interval = getattr(price.recurring, "interval", "month") or "month"

        plans.append({
            "external_plan_id": price.id,
            "name": product_name,
            "base_amount_cents": price.unit_amount or 0,
            "base_currency": (price.currency or "usd").upper(),
            "billing_interval": interval,
        })

    return plans
