"""
Integrations Sync Service — orchestrates connector execution and Plan persistence.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.integration import Integration
from app.models.plan import Plan
from app.integrations.stripe_connector import fetch_stripe_plans
from app.integrations.chargebee_connector import fetch_chargebee_plans
from app.integrations.recurly_connector import fetch_recurly_plans


def sync_integration(
    db: Session,
    integration: Integration,
    credentials: dict | None = None,
) -> list[Plan]:
    """
    Sync plans from connected billing provider into Velo plans table.
    Updates integration status to 'live' on success or 'error' on failure.
    """
    credentials = credentials or {}
    integration.status = "syncing"
    db.commit()

    try:
        provider = integration.provider.lower()
        fetched_plans = []

        if provider == "stripe":
            api_key = credentials.get("api_key") or "sk_test_mock"
            fetched_plans = fetch_stripe_plans(api_key)
        elif provider == "chargebee":
            site = credentials.get("site", "demo-site")
            api_key = credentials.get("api_key", "test_key")
            fetched_plans = fetch_chargebee_plans(site, api_key)
        elif provider == "recurly":
            api_key = credentials.get("api_key", "test_key")
            fetched_plans = fetch_recurly_plans(api_key)
        else:
            raise ValueError(f"Unsupported provider '{integration.provider}'")

        synced_plans = []
        now = datetime.now(timezone.utc)

        for p_data in fetched_plans:
            existing = (
                db.query(Plan)
                .filter(
                    Plan.org_id == integration.org_id,
                    Plan.external_plan_id == p_data["external_plan_id"],
                )
                .first()
            )
            if existing:
                existing.name = p_data["name"]
                existing.base_amount_cents = p_data["base_amount_cents"]
                existing.base_currency = p_data["base_currency"]
                existing.billing_interval = p_data["billing_interval"]
                existing.synced_at = now
                existing.integration_id = integration.id
                synced_plans.append(existing)
            else:
                plan = Plan(
                    org_id=integration.org_id,
                    integration_id=integration.id,
                    external_plan_id=p_data["external_plan_id"],
                    name=p_data["name"],
                    base_amount_cents=p_data["base_amount_cents"],
                    base_currency=p_data["base_currency"],
                    billing_interval=p_data["billing_interval"],
                    synced_at=now,
                )
                db.add(plan)
                synced_plans.append(plan)

        integration.status = "live"
        integration.last_synced_at = now
        integration.last_error = None
        db.commit()
        return synced_plans

    except Exception as e:
        integration.status = "error"
        integration.last_error = str(e)
        db.commit()
        raise e
