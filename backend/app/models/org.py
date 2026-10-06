"""
Org model — the tenant root entity.
Each SaaS company using Velo is represented as one Org.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Org(Base):
    __tablename__ = "orgs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan_tier: Mapped[str] = mapped_column(
        String(50), nullable=False, default="free"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="org", cascade="all, delete-orphan"
    )
    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey", back_populates="org", cascade="all, delete-orphan"
    )
    integrations: Mapped[list["Integration"]] = relationship(
        "Integration", back_populates="org", cascade="all, delete-orphan"
    )
    plans: Mapped[list["Plan"]] = relationship(
        "Plan", back_populates="org", cascade="all, delete-orphan"
    )
    rule_sets: Mapped[list["RuleSet"]] = relationship(
        "RuleSet", back_populates="org", cascade="all, delete-orphan"
    )
    activity_logs: Mapped[list["ActivityLog"]] = relationship(
        "ActivityLog", back_populates="org", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Org id={self.id!r} name={self.name!r}>"
