from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    return jwt.encode({"sub": subject, "exp": expire, "type": "access"}, settings.jwt_secret_key, settings.jwt_algorithm)


def create_refresh_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(UTC) + (expires_delta or timedelta(days=settings.refresh_token_expire_days))
    return jwt.encode(
        {"sub": subject, "exp": expire, "type": "refresh"},
        settings.jwt_refresh_secret_key,
        settings.jwt_algorithm,
    )


def decode_token(token: str, refresh: bool = False) -> dict[str, Any]:
    key = settings.jwt_refresh_secret_key if refresh else settings.jwt_secret_key
    payload = jwt.decode(token, key, algorithms=[settings.jwt_algorithm])
    token_type = payload.get("type")
    expected = "refresh" if refresh else "access"
    if token_type != expected:
        raise JWTError("Invalid token type")
    return payload

