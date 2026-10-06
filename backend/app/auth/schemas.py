"""
Pydantic schemas for authentication endpoints.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ── Signup / Login ─────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    org_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    org_id: str
    user_id: str
    role: str


# ── API Key ────────────────────────────────────────────────────────────────────

class APIKeyCreateRequest(BaseModel):
    label: str = Field(default="Default", max_length=255)


class APIKeyResponse(BaseModel):
    id: str
    label: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    # raw_key is only present at creation time; never returned again
    raw_key: Optional[str] = None

    model_config = {"from_attributes": True}


class APIKeyCreatedResponse(BaseModel):
    """Returned exactly once at key creation — includes raw key."""
    id: str
    label: str
    raw_key: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── User / Org info ────────────────────────────────────────────────────────────

class MeResponse(BaseModel):
    user_id: str
    email: str
    role: str
    org_id: str
    org_name: str
