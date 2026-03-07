import secrets
from typing import Optional

from fastapi import Header, HTTPException, status

# Single active session — single-user monitoring tool
_session_token: Optional[str] = None


def create_session() -> str:
    global _session_token
    _session_token = secrets.token_urlsafe(32)
    return _session_token


def clear_session() -> None:
    global _session_token
    _session_token = None


def is_authenticated(token: Optional[str]) -> bool:
    return bool(token and token == _session_token)


async def require_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    if not is_authenticated(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing session token",
        )
    return x_api_key
