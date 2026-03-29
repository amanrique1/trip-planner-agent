import logging
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer
from jose import JWTError, jwt

from config import Settings, get_settings

logger = logging.getLogger(__name__)

_basic_security = HTTPBasic()
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# bcrypt helpers (no passlib)

def verify_password(plain: str, hashed: str) -> bool:
    """Check a plain password against a bcrypt hash. Never throws."""
    try:
        return bcrypt.checkpw(
            plain.encode("utf-8"),
            hashed.encode("utf-8"),
        )
    except Exception as exc:
        logger.error("Password verification error: %s", exc)
        return False


def hash_password(plain: str, rounds: int = 12) -> str:
    """Return a bcrypt hash of the plain-text password."""
    return bcrypt.hashpw(
        plain.encode("utf-8"),
        bcrypt.gensalt(rounds=rounds),
    ).decode("utf-8")


# admin hash resolution

def _is_valid_bcrypt(value: str) -> bool:
    """A bcrypt hash is 60 chars and starts with $2b$, $2a$, or $2y$."""
    return (
        isinstance(value, str)
        and len(value) == 60
        and value.startswith(("$2b$", "$2a$", "$2y$"))
    )


def _resolve_admin_hash(settings: Settings) -> str:
    """
    Return a valid bcrypt hash for the admin user.

    Priority:
      1. ADMIN_PASSWORD_HASH  (must look like a real bcrypt string)
      2. ADMIN_PASSWORD_HASH  that is actually plain text → hash it (warn)
      3. ADMIN_PASSWORD_PLAIN (dev fallback → hash it at startup)
      4. Crash loudly so the operator notices immediately.
    """
    if settings.admin_password_hash:
        if _is_valid_bcrypt(settings.admin_password_hash):
            logger.info("Admin password: using pre-computed bcrypt hash ✓")
            return settings.admin_password_hash

        # They put a plain password in the _HASH variable
        logger.warning(
            "ADMIN_PASSWORD_HASH is set but is NOT a valid bcrypt hash. "
            "Auto-hashing it now. Please generate a proper hash:\n"
            "    uv run scripts/hash_creator.py"
        )
        return hash_password(settings.admin_password_hash)

    if settings.admin_password_plain:
        logger.warning(
            "Using ADMIN_PASSWORD_PLAIN (hashed at startup). "
            "Fine for dev, bad for production. Generate a hash:\n"
            "    uv run scripts/hash_creator.py"
        )
        return hash_password(settings.admin_password_plain)

    raise RuntimeError(
        "\n╔══════════════════════════════════════════════════════╗\n"
        "║  No admin password configured!                       ║\n"
        "║                                                      ║\n"
        "║  Set one of these in .env:                           ║\n"
        "║    ADMIN_PASSWORD_HASH=\"$2b$12$...\"  (recommended)   ║\n"
        "║    ADMIN_PASSWORD_PLAIN=\"mypass\"     (dev only)      ║\n"
        "║                                                      ║\n"
        "║  Generate a hash:                                    ║\n"
        "║    uv run scripts/hash_creator.py                    ║\n"
        "╚══════════════════════════════════════════════════════╝"
    )


# Resolve ONCE at import time
_admin_hash: str = _resolve_admin_hash(get_settings())


def _get_user_db() -> dict[str, str]:
    return {get_settings().admin_username: _admin_hash}


# JWT helpers

def create_access_token(subject: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes,
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> str:
    """Return the username from the token, or raise 401."""
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        username: str | None = payload.get("sub")
        if not username:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception


# FastAPI dependencies

def authenticate_basic(
    credentials: HTTPBasicCredentials = Depends(_basic_security),
) -> str:
    """Validate HTTP-Basic credentials → return username."""
    db = _get_user_db()
    stored_hash = db.get(credentials.username)
    if not stored_hash or not verify_password(credentials.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def get_current_user(token: str = Depends(_oauth2_scheme)) -> str:
    """Validate Bearer JWT → return username."""
    return decode_access_token(token)