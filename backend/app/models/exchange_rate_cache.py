"""
ExchangeRateCache model — stores the most recent FX rate for a currency pair.
Rate is stored as a string to preserve decimal precision (no float arithmetic).
Refreshed hourly by the FX sync Celery job.
"""
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ExchangeRateCache(Base):
    __tablename__ = "exchange_rate_cache"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)   # ISO 4217
    target_currency: Mapped[str] = mapped_column(String(3), nullable=False) # ISO 4217
    # Stored as string to avoid floating-point representation errors
    rate: Mapped[str] = mapped_column(String(30), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    is_stale: Mapped[bool] = mapped_column(
        default=False, nullable=False
    )  # True when provider was unavailable and this is a fallback value

    __table_args__ = (
        UniqueConstraint("base_currency", "target_currency", name="uq_fx_pair"),
    )

    def __repr__(self) -> str:
        return (
            f"<ExchangeRateCache {self.base_currency}->{self.target_currency} "
            f"rate={self.rate} stale={self.is_stale}>"
        )
