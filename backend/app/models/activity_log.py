"""
ActivityLog model — append-only audit log of every /v1/* API call.
Writes are asynchronous so logging never adds latency to translation responses.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    api_key_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True, index=True
    )
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    region: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # country/currency code
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    request_summary: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Sanitized, no PII
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Relationships
    org: Mapped["Org"] = relationship("Org", back_populates="activity_logs")
    api_key: Mapped[Optional["APIKey"]] = relationship("APIKey", back_populates="activity_logs")

    def __repr__(self) -> str:
        return (
            f"<ActivityLog id={self.id!r} endpoint={self.endpoint!r} "
            f"status={self.status_code} at={self.created_at}>"
        )
