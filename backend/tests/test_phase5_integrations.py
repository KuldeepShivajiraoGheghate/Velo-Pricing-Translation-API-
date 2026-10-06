"""
Phase 5 — Billing Integrations Tests
Tests Stripe, Chargebee, Recurly connectors and sync service.
"""
from unittest.mock import patch, MagicMock
import pytest
from sqlalchemy.orm import Session

from app.models.org import Org
from app.models.integration import Integration
from app.models.plan import Plan
from app.integrations.service import sync_integration


@pytest.fixture
def org_and_integration(db_session: Session):
    org = Org(name="Integration Test Org")
    db_session.add(org)
    db_session.flush()

    integration = Integration(
        org_id=org.id,
        provider="stripe",
        status="disconnected",
    )
    db_session.add(integration)
    db_session.commit()
    return org, integration


def test_sync_stripe_success(db_session: Session, org_and_integration):
    org, integration = org_and_integration

    mock_price = MagicMock()
    mock_price.id = "price_mock_123"
    mock_price.product.name = "Pro Tier"
    mock_price.unit_amount = 4900
    mock_price.currency = "usd"
    mock_price.recurring.interval = "month"

    mock_list_response = MagicMock()
    mock_list_response.data = [mock_price]

    with patch("stripe.Price.list", return_value=mock_list_response):
        plans = sync_integration(db_session, integration, credentials={"api_key": "sk_test_123"})
        assert integration.status == "live"
        assert len(plans) == 1
        assert plans[0].name == "Pro Tier"
        assert plans[0].base_amount_cents == 4900
        assert plans[0].base_currency == "USD"


def test_sync_integration_failure_handles_error(db_session: Session, org_and_integration):
    org, integration = org_and_integration

    with patch("stripe.Price.list", side_effect=Exception("API Connection Failed")):
        with pytest.raises(Exception):
            sync_integration(db_session, integration, credentials={"api_key": "sk_test_bad"})

        db_session.refresh(integration)
        assert integration.status == "error"
        assert "API Connection Failed" in integration.last_error
