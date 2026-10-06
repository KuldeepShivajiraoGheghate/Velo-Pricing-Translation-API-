"""
Tests for Phase 3 - Rates & Tax Data Sync.
"""
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal

from app.models.exchange_rate_cache import ExchangeRateCache
from app.models.tax_rate_reference import TaxRateReference
from app.rates_sync.fx import sync_fx_rates
from app.rates_sync.tax import sync_tax_rates


def test_sync_fx_rates_success(db_session):
    """Test that fx sync correctly fetches and saves rates to DB."""
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "amount": 1.0,
        "base": "USD",
        "date": "2026-09-23",
        "rates": {
            "EUR": 0.85,
            "GBP": 0.75
        }
    }
    
    with patch("httpx.get", return_value=mock_response):
        with patch("app.rates_sync.fx.SessionLocal", return_value=MagicMock(__enter__=lambda _: db_session, __exit__=lambda *args: None)):
            sync_fx_rates()
        
    # Check DB
    eur_rate = db_session.query(ExchangeRateCache).filter_by(base_currency="USD", target_currency="EUR").first()
    assert eur_rate is not None
    assert eur_rate.rate == "0.85"
    
    gbp_rate = db_session.query(ExchangeRateCache).filter_by(base_currency="USD", target_currency="GBP").first()
    assert gbp_rate is not None
    assert gbp_rate.rate == "0.75"


def test_sync_tax_rates_success(db_session):
    """Test that tax sync reads the config and saves to DB."""
    
    mock_tax_data = {
        "tax_rates": [
            {
                "country_code": "US",
                "standard_rate": 0.0,
                "type": "none"
            },
            {
                "country_code": "UK",
                "standard_rate": 20.0,
                "type": "VAT"
            }
        ]
    }
    
    # Mock both the exists() check and the file read
    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open", return_value=MagicMock(__enter__=lambda _: MagicMock(read=lambda: '{"tax_rates": []}'))) as mock_open:
            with patch("json.load", return_value=mock_tax_data):
                with patch("app.rates_sync.tax.SessionLocal", return_value=MagicMock(__enter__=lambda _: db_session, __exit__=lambda *args: None)):
                    sync_tax_rates()
                
    # Check DB
    uk_tax = db_session.query(TaxRateReference).filter_by(country_code="UK").first()
    assert uk_tax is not None
    assert uk_tax.standard_rate == "20.0"
    
    us_tax = db_session.query(TaxRateReference).filter_by(country_code="US").first()
    assert us_tax is not None
    assert us_tax.standard_rate == "0.0"
