"""
API Key authentication dependency for public /v1/* endpoints.
Completely separate from JWT session auth used by the dashboard.
"""
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_api_key
from app.models.api_key import APIKey

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key(
    raw_key: str = Security(_api_key_header),
    db: Session = Depends(get_db),
) -> APIKey:
    """
    Validate an API key from the X-API-Key header.
    - Hashes the incoming key (SHA-256) and looks it up in the DB.
    - Rejects revoked keys.
    - Updates last_used_at on every successful call.
    """
    if not raw_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Pass it via the X-API-Key header.",
        )

    key_hash = hash_api_key(raw_key)
    api_key = db.query(APIKey).filter(APIKey.key_hash == key_hash).first()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )
    if api_key.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has been revoked.",
        )

    # Touch last_used_at
    api_key.last_used_at = datetime.now(timezone.utc)
    db.commit()

    return api_key
