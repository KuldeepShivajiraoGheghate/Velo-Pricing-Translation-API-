"""
RegulationProfile model — reference/config table.
Seeded from config/regulation_profiles.json on startup.
Adding a new profile requires only a new JSON entry, not a code change (NFR-MAINT-1).
"""
from sqlalchemy import String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RegulationProfile(Base):
    __tablename__ = "regulation_profiles"

    # Code is the primary key — e.g. "EU_VAT_GDPR"
    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    # Comma-separated ISO 3166-1 alpha-2 country codes
    applicable_countries: Mapped[str] = mapped_column(Text, nullable=False, default="")
    default_tax_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default="exclusive"
    )  # "inclusive" | "exclusive"
    compliance_note: Mapped[str] = mapped_column(Text, nullable=True)
    tax_type: Mapped[str] = mapped_column(String(20), nullable=False, default="VAT")

    @property
    def applicable_countries_list(self) -> list[str]:
        return [c.strip() for c in self.applicable_countries.split(",") if c.strip()]

    def __repr__(self) -> str:
        return f"<RegulationProfile code={self.code!r} name={self.display_name!r}>"
