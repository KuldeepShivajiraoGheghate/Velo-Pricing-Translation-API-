"""
RuleSet model — versioned configuration for pricing translation.
Only one RuleSet per Org may have is_active=True at any time.
currencies stored as comma-separated ISO codes (simple, avoids JSON column portability issues).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Boolean, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RuleSet(Base):
    __tablename__ = "rule_sets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # Comma-separated ISO 4217 codes, e.g. "EUR,GBP,JPY,AUD"
    currencies: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # FK to regulation_profiles.code (reference table)
    regulation_profile: Mapped[str] = mapped_column(String(50), nullable=False, default="NO_TAX")
    # "inclusive" | "exclusive"
    tax_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="exclusive")
    # "whole" | "nearest_99" | "nearest_00"
    rounding_strategy: Mapped[str] = mapped_column(String(20), nullable=False, default="nearest_99")
    psychological_pricing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    deployed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    org: Mapped["Org"] = relationship("Org", back_populates="rule_sets")

    @property
    def currencies_list(self) -> list[str]:
        """Return currencies as a list of ISO codes."""
        return [c.strip() for c in self.currencies.split(",") if c.strip()]

    def __repr__(self) -> str:
        return (
            f"<RuleSet id={self.id!r} org_id={self.org_id!r} "
            f"version={self.version} active={self.is_active}>"
        )
