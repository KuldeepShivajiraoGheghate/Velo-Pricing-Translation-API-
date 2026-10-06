"""
Integration model — represents a connected billing platform (Stripe, Chargebee, Recurly).
Credentials are NOT stored here; they live in encrypted form and are referenced by
credentials_ref (an opaque key into the secrets store / encrypted env).
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Integration(Base):
    __tablename__ = "integrations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "stripe" | "chargebee" | "recurly"
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="disconnected"
    )  # "live" | "syncing" | "error" | "disconnected"
    credentials_ref: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # Opaque reference to encrypted credential store — NEVER the raw key
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    org: Mapped["Org"] = relationship("Org", back_populates="integrations")
    plans: Mapped[list["Plan"]] = relationship(
        "Plan", back_populates="integration", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Integration id={self.id!r} provider={self.provider!r} status={self.status!r}>"
