"""
Phase 4 — Public Translation API Tests
Tests POST /v1/translate and GET /v1/prices/{plan_id}
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.org import Org
from app.models.user import User
from app.models.api_key import APIKey
from app.models.plan import Plan
from app.models.rule_set import RuleSet
from app.models.exchange_rate_cache import ExchangeRateCache
from app.models.tax_rate_reference import TaxRateReference
from app.core.security import generate_api_key, hash_api_key, hash_password


@pytest.fixture
def test_setup(db_session: Session):
    """Sets up an org, user, active API key, and sample plan/rates for testing."""
    # Org
    org = Org(name="Acme Corp")
    db_session.add(org)
    db_session.flush()

    # User
    user = User(
        org_id=org.id,
        email=f"testpublic_{org.id[:8]}@acme.com",
        password_hash=hash_password("password123"),
        role="admin",
    )
    db_session.add(user)

    # Active API key
    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)
    api_key = APIKey(org_id=org.id, key_hash=key_hash, label="Test Public Key")
    db_session.add(api_key)

    # Active RuleSet
    rule_set = RuleSet(
        org_id=org.id,
        version=1,
        currencies="EUR,GBP,JPY",
        regulation_profile="EU_VAT_GDPR",
        tax_mode="exclusive",
        rounding_strategy="nearest_99",
        psychological_pricing=False,
        is_active=True,
    )
    db_session.add(rule_set)

    # FX Rate check or create
    fx = (
        db_session.query(ExchangeRateCache)
        .filter_by(base_currency="USD", target_currency="EUR")
        .first()
    )
    if not fx:
        fx = ExchangeRateCache(base_currency="USD", target_currency="EUR", rate="0.92")
        db_session.add(fx)

    # Tax Rate check or create
    tax = (
        db_session.query(TaxRateReference)
        .filter_by(country_code="DE", tax_type="VAT")
        .first()
    )
    if not tax:
        tax = TaxRateReference(country_code="DE", tax_type="VAT", standard_rate="19")
        db_session.add(tax)

    # Plan
    plan = Plan(
        org_id=org.id,
        external_plan_id=f"plan_pro_{org.id[:8]}",
        name="Pro Plan",
        base_amount_cents=2900,  # $29.00
        base_currency="USD",
        billing_interval="month",
    )
    db_session.add(plan)

    db_session.commit()

    return {
        "org": org,
        "raw_key": raw_key,
        "api_key": api_key,
        "plan": plan,
    }


def test_translate_unauthorized_without_key(client: TestClient):
    res = client.post(
        "/v1/translate",
        json={
            "amount": "29.00",
            "base_currency": "USD",
            "target_currency": "EUR",
        },
    )
    assert res.status_code == 401


def test_translate_unauthorized_invalid_key(client: TestClient):
    res = client.post(
        "/v1/translate",
        headers={"X-API-Key": "velo_live_invalidkey1234567890"},
        json={
            "amount": "29.00",
            "base_currency": "USD",
            "target_currency": "EUR",
        },
    )
    assert res.status_code == 401


def test_translate_success(client: TestClient, test_setup: dict):
    raw_key = test_setup["raw_key"]
    res = client.post(
        "/v1/translate",
        headers={"X-API-Key": raw_key},
        json={
            "amount": "29.00",
            "base_currency": "USD",
            "target_currency": "EUR",
            "target_country": "DE",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["original_currency"] == "USD"
    assert data["target_currency"] == "EUR"
    assert "translated_amount" in data
    assert "19% tax" in data["tax_label"]
    assert data["rule_set_version"] == "v1"


def test_get_plan_price_success(client: TestClient, test_setup: dict):
    raw_key = test_setup["raw_key"]
    plan = test_setup["plan"]
    res = client.get(
        f"/v1/prices/{plan.id}?target_currency=EUR&target_country=DE",
        headers={"X-API-Key": raw_key},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["plan_id"] == plan.id
    assert data["plan_name"] == "Pro Plan"
    assert data["target_currency"] == "EUR"
    assert "translated_amount" in data


def test_get_plan_price_not_found(client: TestClient, test_setup: dict):
    raw_key = test_setup["raw_key"]
    res = client.get(
        "/v1/prices/nonexistent_id?target_currency=EUR",
        headers={"X-API-Key": raw_key},
    )
    assert res.status_code == 404
