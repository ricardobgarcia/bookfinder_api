import os
from typing import Any, Dict, Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .jwt import decode_token


bearer = HTTPBearer(auto_error=False)


def require_admin_or_cron(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    x_cron_token: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    if x_cron_token:
        expected = os.getenv("CRON_TOKEN")
        if not expected:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="CRON_TOKEN is not configured",
            )
        if x_cron_token != expected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid cron token",
            )
        return {"auth": "cron"}

    if creds is None or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token or x-cron-token",
        )

    try:
        claims = decode_token(creds.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    if claims.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only",
        )

    return {"auth": "jwt", "sub": claims.get("sub"), "role": claims.get("role")}
