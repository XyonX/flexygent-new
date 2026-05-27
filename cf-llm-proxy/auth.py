"""
Authentication middleware for the Cloudflare LLM Proxy.
Handles API key validation for both proxy users and admin endpoints.
"""

from fastapi import Header, HTTPException, status
from typing import Optional

from database import validate_api_key
from config import settings


async def verify_proxy_api_key(authorization: Optional[str] = Header(None)) -> None:
    """
    Dependency that validates the proxy API key from the Authorization header.
    Used for OpenAI-compatible endpoints (/v1/*).
    Expects: Authorization: Bearer <proxy-api-key>
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Use: Bearer <key>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    key_record = validate_api_key(token)
    if key_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_admin_key(authorization: Optional[str] = Header(None)) -> None:
    """
    Dependency that validates the admin API key from the Authorization header.
    Used for admin endpoints (/admin/*).
    Expects: Authorization: Bearer <admin-api-key>
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Use: Bearer <key>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
