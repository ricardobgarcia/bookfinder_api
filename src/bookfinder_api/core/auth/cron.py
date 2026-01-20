import os
from fastapi import Header, HTTPException, status


def require_cron_token(x_cron_token: str | None = Header(default=None)) -> None:
    expected = os.getenv("CRON_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CRON_TOKEN is not configured",
        )

    if not x_cron_token or x_cron_token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cron token",
        )
