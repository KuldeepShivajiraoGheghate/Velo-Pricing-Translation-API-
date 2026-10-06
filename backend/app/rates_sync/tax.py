import json
from pathlib import Path
from decimal import Decimal
import structlog
from celery import shared_task

from app.core.database import SessionLocal
from app.models.tax_rate_reference import TaxRateReference

logger = structlog.get_logger()

# Path to the bundled tax config
TAX_CONFIG_PATH = Path(__file__).parent.parent / "config" / "tax_rates.json"


@shared_task
def sync_tax_rates():
    """
    Sync tax rates from the bundled tax_rates.json config file into the database.
    This satisfies NFR-MAINT-1 (data-driven tax rates).
    """
    logger.info("Starting Tax rate sync")
    
    if not TAX_CONFIG_PATH.exists():
        logger.error(f"Tax config file not found at {TAX_CONFIG_PATH}")
        return

    try:
        with open(TAX_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        tax_rates = data.get("tax_rates", [])
        
        with SessionLocal() as db:
            updated_count = 0
            for item in tax_rates:
                country_code = item.get("country_code")
                tax_type = item.get("type", "NONE")
                standard_rate = str(item.get("standard_rate", "0.0"))
                
                existing = db.query(TaxRateReference).filter(
                    TaxRateReference.country_code == country_code,
                    TaxRateReference.tax_type == tax_type
                ).first()
                if existing:
                    existing.standard_rate = standard_rate
                else:
                    new_tax = TaxRateReference(
                        country_code=country_code,
                        tax_type=tax_type,
                        standard_rate=standard_rate
                    )
                    db.add(new_tax)
                
                updated_count += 1
                
            db.commit()
            logger.info(f"Successfully synced {updated_count} tax rates")
            
    except Exception as e:
        logger.error("Tax sync failed", error=str(e))
        raise
