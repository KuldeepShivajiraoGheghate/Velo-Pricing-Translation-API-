"""
Pydantic schemas for the public /v1/ API endpoints.
"""
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class TranslateRequest(BaseModel):
    """POST /v1/translate request body."""
    amount: Decimal = Field(..., description="Base price amount (decimal, not float)")
    base_currency: str = Field(..., min_length=3, max_length=3, description="ISO 4217 source currency")
    target_currency: str = Field(..., min_length=3, max_length=3, description="ISO 4217 target currency")
    target_country: Optional[str] = Field(None, min_length=2, max_length=2, description="ISO 3166-1 country code for tax lookup")


class TranslateResponse(BaseModel):
    """POST /v1/translate response body."""
    original_amount: Decimal
    original_currency: str
    translated_amount: Decimal
    target_currency: str
    tax_label: str
    regulation_notes: str
    rule_set_version: str


class PlanPriceResponse(BaseModel):
    """Single plan price translation result."""
    plan_id: str
    plan_name: str
    base_amount_cents: int
    base_currency: str
    translated_amount: Decimal
    target_currency: str
    billing_interval: str
    tax_label: str
    rule_set_version: str


class PlanPricesResponse(BaseModel):
    """GET /v1/prices/{plan_id} or list response."""
    prices: list[PlanPriceResponse]
