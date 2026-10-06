"""
Recurly Connector — syncs plans from Recurly into Velo Plan format.
"""
import httpx


def fetch_recurly_plans(api_key: str) -> list[dict]:
    """
    Fetch active plans from Recurly v3 REST API and normalize into Velo Plan dicts.
    """
    if not api_key:
        raise ValueError("Recurly API key is required.")

    url = "https://v3.recurly.com/plans"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/vnd.recurly.v2021-02-25",
    }
    response = httpx.get(url, headers=headers, timeout=10.0)
    response.raise_for_request()

    data = response.json()
    plans = []

    for p in data.get("data", []):
        # Recurly pricing is array of currencies
        pricing = p.get("currencies", [])
        amount = 0
        currency = "USD"
        if pricing:
            amount = int(pricing[0].get("unit_amount", 0) * 100)
            currency = pricing[0].get("currency", "USD").upper()

        plans.append({
            "external_plan_id": p.get("code") or p.get("id"),
            "name": p.get("name", "Plan"),
            "base_amount_cents": amount,
            "base_currency": currency,
            "billing_interval": p.get("interval_unit", "month").lower(),
        })

    return plans
