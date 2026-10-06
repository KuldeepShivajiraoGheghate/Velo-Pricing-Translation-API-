import httpx
from datetime import datetime, timezone
import structlog
from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from decimal import Decimal

from app.core.database import SessionLocal
from app.models.exchange_rate_cache import ExchangeRateCache

logger = structlog.get_logger()

# Frankfurter API is free and open-source, uses ECB data
FRANKFURTER_API_URL = "https://api.frankfurter.app/latest"


@shared_task
def sync_fx_rates():
    """
    Sync FX rates from Frankfurter API to the database.
    We fetch rates relative to USD as a base for standard storage, 
    but we can also just fetch the default (EUR base) and compute cross rates.
    For simplicity, let's fetch with base=USD.
    """
    logger.info("Starting FX rate sync")
    
    try:
        # Fetch rates with base USD
        response = httpx.get(f"{FRANKFURTER_API_URL}?from=USD")
        response.raise_for_status()
        data = response.json()
        
        rates = data.get("rates", {})
        if not rates:
            logger.error("No rates found in response")
            return
            
        # Frankfurter doesn't include the base currency in the rates dict (USD to USD is 1.0)
        rates["USD"] = 1.0

        with SessionLocal() as db:
            updated_count = 0
            for currency, rate in rates.items():
                if currency == "USD":
                    continue # Usually skip self, but keeping for completeness if needed
                    
                # We store pairs like base_currency="USD", target_currency=currency
                
                # Check if pair exists
                existing = db.query(ExchangeRateCache).filter(
                    ExchangeRateCache.base_currency == "USD",
                    ExchangeRateCache.target_currency == currency
                ).first()
                if existing:
                    existing.rate = str(rate)
                    existing.fetched_at = datetime.now(timezone.utc)
                    existing.is_stale = False
                else:
                    new_rate = ExchangeRateCache(
                        base_currency="USD",
                        target_currency=currency,
                        rate=str(rate),
                        fetched_at=datetime.now(timezone.utc),
                        is_stale=False
                    )
                    db.add(new_rate)
                
                updated_count += 1
                
            db.commit()
            logger.info(f"Successfully updated {updated_count} FX rates")
            
    except Exception as e:
        logger.error("FX sync failed", error=str(e))
        raise
