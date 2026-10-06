"""
Admin/Internal API (/api/*) — powers the Velo Dashboard shell.
Authenticated via User JWT Session (get_current_user).
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.integration import Integration
from app.models.rule_set import RuleSet
from app.models.plan import Plan
from app.models.activity_log import ActivityLog
from app.models.api_key import APIKey
from app.models.exchange_rate_cache import ExchangeRateCache
from app.models.tax_rate_reference import TaxRateReference
from app.core.security import generate_api_key, hash_api_key
from app.rules_engine.engine import translate
from app.integrations.service import sync_integration
from app.admin_api.schemas import (
    IntegrationResponse,
    ConnectIntegrationRequest,
    RuleSetRequest,
    RuleSetResponse,
    PreviewRequest,
    PreviewResponse,
    ActivityLogResponse,
    APIKeyCreateRequest,
    APIKeyResponse,
)

router = APIRouter(tags=["admin-api"])


# ── Integrations ────────────────────────────────────────────────────────────────

@router.get("/integrations", response_model=list[IntegrationResponse])
def list_integrations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all integrations connected for the user's organization."""
    return (
        db.query(Integration)
        .filter(Integration.org_id == current_user.org_id)
        .order_by(Integration.created_at.desc())
        .all()
    )


@router.post("/integrations/connect", response_model=IntegrationResponse)
def connect_integration(
    body: ConnectIntegrationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Connect a new billing provider (Stripe, Chargebee, Recurly) and sync plans."""
    existing = (
        db.query(Integration)
        .filter(
            Integration.org_id == current_user.org_id,
            Integration.provider == body.provider.lower(),
        )
        .first()
    )

    if not existing:
        existing = Integration(
            org_id=current_user.org_id,
            provider=body.provider.lower(),
            status="syncing",
        )
        db.add(existing)
        db.commit()
        db.refresh(existing)

    credentials = {"api_key": body.api_key, "site": body.site}
    try:
        sync_integration(db, existing, credentials=credentials)
    except Exception:
        pass  # sync_integration updates existing.status = 'error' and commits

    return existing


@router.post("/integrations/{integration_id}/sync", response_model=IntegrationResponse)
def sync_integration_endpoint(
    integration_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger manual re-sync of an integration."""
    integration = (
        db.query(Integration)
        .filter(
            Integration.id == integration_id,
            Integration.org_id == current_user.org_id,
        )
        .first()
    )
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found.")

    try:
        sync_integration(db, integration)
    except Exception:
        pass

    return integration


# ── RuleSets (Rules Engine Configuration) ───────────────────────────────────────

@router.get("/rules/active", response_model=Optional[RuleSetResponse])
def get_active_ruleset(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get currently active RuleSet for the organization."""
    rule_set = (
        db.query(RuleSet)
        .filter(RuleSet.org_id == current_user.org_id, RuleSet.is_active == True)
        .order_by(RuleSet.version.desc())
        .first()
    )
    if not rule_set:
        return None

    return RuleSetResponse(
        id=rule_set.id,
        version=rule_set.version,
        currencies=rule_set.currencies_list,
        regulation_profile=rule_set.regulation_profile,
        tax_mode=rule_set.tax_mode,
        rounding_strategy=rule_set.rounding_strategy,
        psychological_pricing=rule_set.psychological_pricing,
        is_active=rule_set.is_active,
        created_at=rule_set.created_at,
        deployed_at=rule_set.deployed_at,
    )


@router.post("/rules", response_model=RuleSetResponse)
def create_and_deploy_ruleset(
    body: RuleSetRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Save and deploy a new version of the RuleSet for the organization.
    Deactivates previous versions and sets the new version as active.
    """
    if not body.currencies:
        raise HTTPException(status_code=400, detail="At least one target currency is required.")

    # Determine next version
    latest = (
        db.query(RuleSet)
        .filter(RuleSet.org_id == current_user.org_id)
        .order_by(RuleSet.version.desc())
        .first()
    )
    next_version = (latest.version + 1) if latest else 1

    # Deactivate prior active rule sets
    db.query(RuleSet).filter(
        RuleSet.org_id == current_user.org_id,
        RuleSet.is_active == True,
    ).update({"is_active": False})

    new_rule_set = RuleSet(
        org_id=current_user.org_id,
        version=next_version,
        currencies=",".join([c.strip().upper() for c in body.currencies]),
        regulation_profile=body.regulation_profile,
        tax_mode=body.tax_mode,
        rounding_strategy=body.rounding_strategy,
        psychological_pricing=body.psychological_pricing,
        is_active=True,
        deployed_at=datetime.now(timezone.utc),
    )
    db.add(new_rule_set)
    db.commit()
    db.refresh(new_rule_set)

    return RuleSetResponse(
        id=new_rule_set.id,
        version=new_rule_set.version,
        currencies=new_rule_set.currencies_list,
        regulation_profile=new_rule_set.regulation_profile,
        tax_mode=new_rule_set.tax_mode,
        rounding_strategy=new_rule_set.rounding_strategy,
        psychological_pricing=new_rule_set.psychological_pricing,
        is_active=new_rule_set.is_active,
        created_at=new_rule_set.created_at,
        deployed_at=new_rule_set.deployed_at,
    )


# ── Plans List & Live Preview ───────────────────────────────────────────────────

@router.get("/plans")
def list_org_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List synced plans for preview dropdown."""
    plans = (
        db.query(Plan)
        .filter(Plan.org_id == current_user.org_id)
        .order_by(Plan.name.asc())
        .all()
    )
    return [
        {
            "id": p.id,
            "name": p.name,
            "base_amount_cents": p.base_amount_cents,
            "base_currency": p.base_currency,
            "billing_interval": p.billing_interval,
        }
        for p in plans
    ]


@router.post("/preview", response_model=PreviewResponse)
def compute_preview(
    body: PreviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compute live translation preview side-by-side with original price."""
    base_amount = Decimal("29.00")
    base_curr = body.base_currency or "USD"

    if body.plan_id:
        plan = (
            db.query(Plan)
            .filter(Plan.id == body.plan_id, Plan.org_id == current_user.org_id)
            .first()
        )
        if plan:
            base_amount = Decimal(str(plan.base_amount_cents)) / Decimal("100")
            base_curr = plan.base_currency
    elif body.amount is not None:
        base_amount = body.amount

    # Fetch active rule set
    rule_set = (
        db.query(RuleSet)
        .filter(RuleSet.org_id == current_user.org_id, RuleSet.is_active == True)
        .order_by(RuleSet.version.desc())
        .first()
    )
    tax_mode = rule_set.tax_mode if rule_set else "exclusive"
    rounding = rule_set.rounding_strategy if rule_set else "nearest_99"
    psych = rule_set.psychological_pricing if rule_set else False
    version = f"v{rule_set.version}" if rule_set else "v1-default"

    # FX & Tax lookup
    fx_rate = Decimal("1.0")
    if base_curr.upper() != body.target_currency.upper():
        cache = (
            db.query(ExchangeRateCache)
            .filter_by(base_currency=base_curr.upper(), target_currency=body.target_currency.upper())
            .first()
        )
        if cache:
            fx_rate = Decimal(str(cache.rate))

    tax_rate = Decimal("0")
    if body.target_country:
        tax_ref = (
            db.query(TaxRateReference)
            .filter_by(country_code=body.target_country.upper())
            .first()
        )
        if tax_ref:
            tax_rate = Decimal(str(tax_ref.standard_rate))

    result = translate(
        amount=base_amount,
        base_currency=base_curr,
        target_currency=body.target_currency,
        fx_rate=fx_rate,
        tax_rate=tax_rate,
        tax_mode=tax_mode,
        rounding_strategy=rounding,
        psychological_pricing=psych,
        rule_set_version=version,
    )

    return PreviewResponse(
        original_amount=base_amount,
        original_currency=base_curr.upper(),
        translated_amount=result.translated_amount,
        target_currency=body.target_currency.upper(),
        tax_label=result.tax_label,
        regulation_notes=result.regulation_notes,
        rule_set_version=result.rule_set_version,
    )


# ── Activity Logs ───────────────────────────────────────────────────────────────

@router.get("/activity", response_model=list[ActivityLogResponse])
def get_activity_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status_code: Optional[int] = Query(None),
    endpoint: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Query activity logs for the user's organization."""
    query = db.query(ActivityLog).filter(ActivityLog.org_id == current_user.org_id)

    if status_code:
        query = query.filter(ActivityLog.status_code == status_code)
    if endpoint:
        query = query.filter(ActivityLog.endpoint.contains(endpoint))
    if region:
        query = query.filter(ActivityLog.region == region.upper())

    logs = (
        query.order_by(ActivityLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return logs


# ── API Keys ────────────────────────────────────────────────────────────────────

@router.get("/keys", response_model=list[APIKeyResponse])
def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List API keys for the user's organization."""
    keys = (
        db.query(APIKey)
        .filter(APIKey.org_id == current_user.org_id)
        .order_by(APIKey.created_at.desc())
        .all()
    )
    return [
        APIKeyResponse(
            id=k.id,
            label=k.label,
            created_at=k.created_at,
            last_used_at=k.last_used_at,
            is_revoked=k.is_revoked,
        )
        for k in keys
    ]


@router.post("/keys", response_model=APIKeyResponse)
def create_api_key(
    body: APIKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a new API key. Raw key returned ONCE in response."""
    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)

    key = APIKey(
        org_id=current_user.org_id,
        key_hash=key_hash,
        label=body.label,
    )
    db.add(key)
    db.commit()
    db.refresh(key)

    return APIKeyResponse(
        id=key.id,
        label=key.label,
        raw_key=raw_key,
        created_at=key.created_at,
        last_used_at=key.last_used_at,
        is_revoked=key.is_revoked,
    )


@router.delete("/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke an API key."""
    key = (
        db.query(APIKey)
        .filter(APIKey.id == key_id, APIKey.org_id == current_user.org_id)
        .first()
    )
    if not key:
        raise HTTPException(status_code=404, detail="API key not found.")

    key.revoked_at = datetime.now(timezone.utc)
    db.commit()
