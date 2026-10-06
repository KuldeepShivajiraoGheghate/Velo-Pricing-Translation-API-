"""
TaxRateReference model — stores tax rate data by country.
Seeded from config/tax_rates.json on startup via the tax sync job.
Rate stored as string to avoid floating-point issues.
"""
from datetime import date, datetime, timezone

from sqlalchemy import String, DateTime, Date, UniqueConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TaxRateReference(Base):
    __tablename__ = "tax_rate_references"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, index=True)  # ISO 3166-1
    tax_type: Mapped[str] = mapped_column(String(30), nullable=False)  # VAT | GST | NONE | OTHER
    # Rates stored as strings to preserve decimal precision
    standard_rate: Mapped[str] = mapped_column(String(10), nullable=False, default="0")
    reduced_rate: Mapped[str] = mapped_column(String(10), nullable=False, default="0")
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("country_code", "tax_type", name="uq_tax_rate"),
    )

    def __repr__(self) -> str:
        return (
            f"<TaxRateReference {self.country_code} {self.tax_type} "
            f"rate={self.standard_rate}%>"
        )
