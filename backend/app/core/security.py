"""
Security utilities — password hashing and JWT token handling.
API key generation and hashing.
"""
import hashlib
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
import bcrypt

from app.core.settings import get_settings

settings = get_settings()

# ── Password utilities ─────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Return a bcrypt hash of the given password."""
    # bcrypt expects and returns bytes, so we encode/decode
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a stored bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


# ── JWT utilities ──────────────────────────────────────────────────────────────

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT. Returns the payload dict, or None if invalid/expired.
    Does NOT raise — callers handle None as an authentication failure.
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


# ── API key utilities ──────────────────────────────────────────────────────────

_API_KEY_PREFIX = "velo_"
_API_KEY_BYTES = 32  # 256-bit random token → 64 hex chars after prefix


def generate_api_key() -> str:
    """
    Generate a cryptographically random API key.
    Format: velo_<64 hex chars>
    The raw key is returned ONCE here; callers must hash it before storing.
    """
    random_part = secrets.token_hex(_API_KEY_BYTES)
    return f"{_API_KEY_PREFIX}{random_part}"


def hash_api_key(raw_key: str) -> str:
    """Return SHA-256 hex digest of the raw API key. This is what's stored in DB."""
    return hashlib.sha256(raw_key.encode()).hexdigest()
