import os
from celery import Celery
from celery.schedules import crontab
from app.core.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "velo_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.rates_sync.fx", "app.rates_sync.tax"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Configure beat schedule
    beat_schedule={
        "sync-fx-rates-daily": {
            "task": "app.rates_sync.fx.sync_fx_rates",
            "schedule": crontab(hour="0", minute="0"),  # Midnight UTC
        },
        "sync-tax-rates-daily": {
            "task": "app.rates_sync.tax.sync_tax_rates",
            "schedule": crontab(hour="1", minute="0"),  # 1 AM UTC
        }
    }
)
