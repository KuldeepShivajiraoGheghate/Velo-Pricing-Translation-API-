"""
Auth router — signup, login, API key management, /me endpoint.
All routes use JWT session auth (not API key auth).
"""
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_admin
from app.auth.schemas import (
    APIKeyCreateRequest,
    APIKeyCreatedResponse,
    APIKeyResponse,
    LoginRequest,
    MeResponse,
    SignupRequest,
    TokenResponse,
)
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    generate_api_key,
    hash_api_key,
    hash_password,
    verify_password,
)
from app.models.api_key import APIKey
from app.models.org import Org
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Signup ─────────────────────────────────────────────────────────────────────

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Create a new Org and its first Admin user.
    Returns a JWT access token immediately so the user is logged in after signup.
    """
    # Check email uniqueness
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Create Org
    org = Org(name=payload.org_name)
    db.add(org)
    db.flush()  # get org.id without committing yet

    # Create User
    user = User(
        org_id=org.id,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "org_id": org.id, "role": user.role})
    return TokenResponse(
        access_token=token,
        org_id=org.id,
        user_id=user.id,
        role=user.role,
    )


# ── Login ──────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate with email + password; returns a JWT access token."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )

    org = db.get(Org, user.org_id)
    token = create_access_token({"sub": user.id, "org_id": user.org_id, "role": user.role})
    return TokenResponse(
        access_token=token,
        org_id=user.org_id,
        user_id=user.id,
        role=user.role,
    )


# ── Me ─────────────────────────────────────────────────────────────────────────

@router.get("/me", response_model=MeResponse)
def me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeResponse:
    """Return the current authenticated user's profile."""
    org = db.get(Org, current_user.org_id)
    return MeResponse(
        user_id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        org_id=current_user.org_id,
        org_name=org.name if org else "",
    )


# ── API Key Management ─────────────────────────────────────────────────────────

@router.post(
    "/keys",
    response_model=APIKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_api_key(
    payload: APIKeyCreateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> APIKeyCreatedResponse:
    """
    Generate a new API key for the Org.
    The raw key is returned exactly once — it cannot be retrieved again.
    """
    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)

    api_key = APIKey(
        org_id=current_user.org_id,
        key_hash=key_hash,
        label=payload.label,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return APIKeyCreatedResponse(
        id=api_key.id,
        label=api_key.label,
        raw_key=raw_key,  # shown ONCE; not stored
        created_at=api_key.created_at,
    )


@router.get("/keys", response_model=List[APIKeyResponse])
def list_api_keys(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> List[APIKeyResponse]:
    """List all API keys for the current Org (hashed — raw keys never returned)."""
    keys = (
        db.query(APIKey)
        .filter(APIKey.org_id == current_user.org_id)
        .order_by(APIKey.created_at.desc())
        .all()
    )
    return [APIKeyResponse.model_validate(k) for k in keys]


@router.delete("/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    key_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    """Revoke an API key. It becomes immediately invalid for /v1/* calls."""
    api_key = (
        db.query(APIKey)
        .filter(APIKey.id == key_id, APIKey.org_id == current_user.org_id)
        .first()
    )
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found.")
    if api_key.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="API key is already revoked."
        )

    api_key.revoked_at = datetime.now(timezone.utc)
    db.commit()


@router.get("/keys/{key_id}", response_model=APIKeyResponse)
def get_api_key(
    key_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> APIKeyResponse:
    """Get a single API key record by ID."""
    api_key = (
        db.query(APIKey)
        .filter(APIKey.id == key_id, APIKey.org_id == current_user.org_id)
        .first()
    )
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found.")
    return APIKeyResponse.model_validate(api_key)
