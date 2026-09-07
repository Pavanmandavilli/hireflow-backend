from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from jose import JWTError, jwt

from app.core.config import get_settings
from app.logging.logger import get_logger

settings = get_settings()
logger = get_logger("jwt-handler")


def _read_key(path: str) -> str:
    return Path(path).read_text()


def create_access_token(subject: str, extra: dict | None = None) -> str:
    """Create a signed RS256 JWT access token."""
    private_key = _read_key(settings.JWT_PRIVATE_KEY_PATH)
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        **(extra or {}),
    }
    return jwt.encode(payload, private_key, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> dict | None:
    """Verify a JWT and return its payload, or None if invalid."""
    public_key = _read_key(settings.JWT_PUBLIC_KEY_PATH)
    try:
        return jwt.decode(token, public_key, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        logger.warning(f"JWT verification failed: {exc}")
        return None
