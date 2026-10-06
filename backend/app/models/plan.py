"""
Plan model — normalized plan/price data from any billing provider.
Populated by integration sync jobs. The Rules Engine and Preview
never need to know which billing provider a plan came from.
Amount stored as integer cents to avoid float issues; base_currency is ISO 4217.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Integer, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    integration_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("integrations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    external_plan_id: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # ID in Stripe/Chargebee/Recurly
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Amount stored in smallest currency unit (e.g. cents for USD/EUR) to avoid float math
    base_amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)  # ISO 4217
    billing_interval: Mapped[str] = mapped_column(
        String(20), nullable=False, default="month"
    )  # "month" | "year" | "week" | "one_time"
    is_active: Mapped[bool] = mapped_column(
        String(1), nullable=False, default=True  # stored as bool via SQLAlchemy
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    org: Mapped["Org"] = relationship("Org", back_populates="plans")
    integration: Mapped[Optional["Integration"]] = relationship(
        "Integration", back_populates="plans"
    )

    def __repr__(self) -> str:
        return (
            f"<Plan id={self.id!r} name={self.name!r} "
            f"amount={self.base_amount_cents} {self.base_currency}>"
        )
