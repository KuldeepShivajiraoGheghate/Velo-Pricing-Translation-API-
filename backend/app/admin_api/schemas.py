"""
Pydantic schemas for the Admin/Dashboard API (/api/*).
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


# ── Integrations ────────────────────────────────────────────────────────────────
class IntegrationResponse(BaseModel):
    id: str
    provider: str
    status: str
    last_synced_at: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime


class ConnectIntegrationRequest(BaseModel):
    provider: str = Field(..., description="stripe | chargebee | recurly")
    api_key: Optional[str] = None
    site: Optional[str] = None


# ── RuleSets ────────────────────────────────────────────────────────────────────
class RuleSetRequest(BaseModel):
    currencies: list[str] = Field(..., description="Target currencies, e.g. ['EUR', 'GBP', 'JPY']")
    regulation_profile: str = Field("EU_VAT_GDPR", description="EU_VAT_GDPR | INDIA_GST | BRAZIL_LGPD")
    tax_mode: str = Field("exclusive", description="inclusive | exclusive")
    rounding_strategy: str = Field("nearest_99", description="whole | nearest_99 | nearest_00")
    psychological_pricing: bool = Field(False)


class RuleSetResponse(BaseModel):
    id: str
    version: int
    currencies: list[str]
    regulation_profile: str
    tax_mode: str
    rounding_strategy: str
    psychological_pricing: bool
    is_active: bool
    created_at: datetime
    deployed_at: Optional[datetime] = None


# ── Preview ─────────────────────────────────────────────────────────────────────
class PreviewRequest(BaseModel):
    plan_id: Optional[str] = None
    amount: Optional[Decimal] = None
    base_currency: Optional[str] = "USD"
    target_currency: str = "EUR"
    target_country: Optional[str] = "DE"


class PreviewResponse(BaseModel):
    original_amount: Decimal
    original_currency: str
    translated_amount: Decimal
    target_currency: str
    tax_label: str
    regulation_notes: str
    rule_set_version: str


# ── Activity ────────────────────────────────────────────────────────────────────
class ActivityLogResponse(BaseModel):
    id: str
    endpoint: str
    status_code: int
    latency_ms: Optional[int] = None
    region: Optional[str] = None
    request_summary: Optional[str] = None
    created_at: datetime


# ── API Keys ────────────────────────────────────────────────────────────────────
class APIKeyCreateRequest(BaseModel):
    label: str = Field(..., max_length=100)


class APIKeyResponse(BaseModel):
    id: str
    label: str
    raw_key: Optional[str] = None
    created_at: datetime
    last_used_at: Optional[datetime] = None
    is_revoked: bool
