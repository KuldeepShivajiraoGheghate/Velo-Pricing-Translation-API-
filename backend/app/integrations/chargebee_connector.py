"""
Chargebee Connector — syncs plans from Chargebee into Velo Plan format.
"""
import httpx


def fetch_chargebee_plans(site: str, api_key: str) -> list[dict]:
    """
    Fetch active plans from Chargebee REST API and normalize into Velo Plan dicts.
    """
    if not site or not api_key:
        raise ValueError("Chargebee site and API key are required.")

    url = f"https://{site}.chargebee.com/api/v2/plans"
    response = httpx.get(
        url,
        auth=(api_key, ""),
        params={"status[is]": "active", "limit": 100},
        timeout=10.0,
    )
    response.raise_for_request()

    data = response.json()
    plans = []

    for item in data.get("list", []):
        p = item.get("plan", {})
        plans.append({
            "external_plan_id": p.get("id"),
            "name": p.get("name", p.get("id")),
            "base_amount_cents": p.get("price", 0),
            "base_currency": (p.get("currency_code") or "USD").upper(),
            "billing_interval": p.get("period_unit", "month").lower(),
        })

    return plans
