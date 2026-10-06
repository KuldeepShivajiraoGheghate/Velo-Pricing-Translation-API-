"""
Public Translation API (/v1/*)
Authenticated via API Key header (X-API-Key).
"""
import time
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.public_api.dependencies import get_api_key
from app.public_api.schemas import (
    TranslateRequest,
    TranslateResponse,
    PlanPriceResponse,
)
from app.models.api_key import APIKey
from app.models.rule_set import RuleSet
from app.models.exchange_rate_cache import ExchangeRateCache
from app.models.tax_rate_reference import TaxRateReference
from app.models.plan import Plan
from app.rules_engine.engine import translate
from app.activity_logging.logger import log_activity

router = APIRouter(prefix="/v1", tags=["public-api"])


def _get_active_ruleset(db: Session, org_id: str) -> RuleSet:
    """Fetch the active rule set for the org or return a default placeholder rule set."""
    rule_set = (
        db.query(RuleSet)
        .filter(RuleSet.org_id == org_id, RuleSet.is_active == True)
        .order_by(RuleSet.version.desc())
        .first()
    )
    if not rule_set:
        # Fallback default rule set if none activated yet
        rule_set = RuleSet(
            org_id=org_id,
            version=1,
            currencies="EUR,GBP,JPY,AUD,CAD,BRL,INR",
            regulation_profile="EU_VAT_GDPR",
            tax_mode="exclusive",
            rounding_strategy="nearest_99",
            psychological_pricing=False,
            is_active=True,
        )
    return rule_set


def _get_fx_rate(db: Session, base: str, target: str) -> Decimal:
    """Look up exchange rate from ExchangeRateCache or default to 1.0 if identical/fallback."""
    if base.upper() == target.upper():
        return Decimal("1.0")

    cache = (
        db.query(ExchangeRateCache)
        .filter(
            ExchangeRateCache.base_currency == base.upper(),
            ExchangeRateCache.target_currency == target.upper(),
        )
        .first()
    )
    if cache:
        try:
            return Decimal(str(cache.rate))
        except Exception:
            return Decimal("1.0")
    return Decimal("1.0")


def _get_tax_rate(db: Session, country_code: Optional[str]) -> Decimal:
    """Look up tax rate from TaxRateReference for country code."""
    if not country_code:
        return Decimal("0")
    ref = (
        db.query(TaxRateReference)
        .filter(TaxRateReference.country_code == country_code.upper())
        .first()
    )
    if ref:
        try:
            return Decimal(str(ref.standard_rate))
        except Exception:
            return Decimal("0")
    return Decimal("0")


@router.post("/translate", response_model=TranslateResponse)
def translate_price_endpoint(
    body: TranslateRequest,
    api_key: APIKey = Depends(get_api_key),
    db: Session = Depends(get_db),
):
    """
    Translate a base amount and currency to a target currency with tax & rounding rules.
    """
    start_time = time.perf_counter()
    rule_set = _get_active_ruleset(db, api_key.org_id)
    fx_rate = _get_fx_rate(db, body.base_currency, body.target_currency)
    tax_rate = _get_tax_rate(db, body.target_country)

    result = translate(
        amount=body.amount,
        base_currency=body.base_currency,
        target_currency=body.target_currency,
        fx_rate=fx_rate,
        tax_rate=tax_rate,
        tax_mode=rule_set.tax_mode,
        rounding_strategy=rule_set.rounding_strategy,
        psychological_pricing=rule_set.psychological_pricing,
        rule_set_version=f"v{rule_set.version}",
    )

    latency_ms = int((time.perf_counter() - start_time) * 1000)

    log_activity(
        org_id=api_key.org_id,
        api_key_id=api_key.id,
        endpoint="/v1/translate",
        status_code=200,
        latency_ms=latency_ms,
        region=body.target_country or body.target_currency,
        request_summary=f"{body.amount} {body.base_currency} -> {result.translated_amount} {body.target_currency}",
    )

    return TranslateResponse(
        original_amount=body.amount,
        original_currency=body.base_currency.upper(),
        translated_amount=result.translated_amount,
        target_currency=body.target_currency.upper(),
        tax_label=result.tax_label,
        regulation_notes=result.regulation_notes,
        rule_set_version=result.rule_set_version,
    )


@router.get("/prices/{plan_id}", response_model=PlanPriceResponse)
def get_plan_price_endpoint(
    plan_id: str,
    target_currency: str = Query(..., min_length=3, max_length=3),
    target_country: Optional[str] = Query(None, min_length=2, max_length=2),
    api_key: APIKey = Depends(get_api_key),
    db: Session = Depends(get_db),
):
    """
    Translate a specific plan's base price into a target currency.
    """
    start_time = time.perf_counter()
    plan = (
        db.query(Plan)
        .filter(
            Plan.org_id == api_key.org_id,
            (Plan.id == plan_id) | (Plan.external_plan_id == plan_id),
        )
        .first()
    )
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan '{plan_id}' not found.",
        )

    base_amount = Decimal(str(plan.base_amount_cents)) / Decimal("100")
    rule_set = _get_active_ruleset(db, api_key.org_id)
    fx_rate = _get_fx_rate(db, plan.base_currency, target_currency)
    tax_rate = _get_tax_rate(db, target_country)

    result = translate(
        amount=base_amount,
        base_currency=plan.base_currency,
        target_currency=target_currency,
        fx_rate=fx_rate,
        tax_rate=tax_rate,
        tax_mode=rule_set.tax_mode,
        rounding_strategy=rule_set.rounding_strategy,
        psychological_pricing=rule_set.psychological_pricing,
        rule_set_version=f"v{rule_set.version}",
    )

    latency_ms = int((time.perf_counter() - start_time) * 1000)

    log_activity(
        org_id=api_key.org_id,
        api_key_id=api_key.id,
        endpoint=f"/v1/prices/{plan_id}",
        status_code=200,
        latency_ms=latency_ms,
        region=target_country or target_currency,
        request_summary=f"Plan {plan.name}: {base_amount} {plan.base_currency} -> {result.translated_amount} {target_currency}",
    )

    return PlanPriceResponse(
        plan_id=plan.id,
        plan_name=plan.name,
        base_amount_cents=plan.base_amount_cents,
        base_currency=plan.base_currency,
        translated_amount=result.translated_amount,
        target_currency=target_currency.upper(),
        billing_interval=plan.billing_interval,
        tax_label=result.tax_label,
        rule_set_version=result.rule_set_version,
    )
