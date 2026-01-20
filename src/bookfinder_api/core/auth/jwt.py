import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import jwt, JWTError


JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALG = os.getenv("JWT_ALG")
ACCESS_TOKEN_EXPIRES_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRES_MIN", "60"))



def create_access_token(subject: str, role: str, expires_minutes: int = ACCESS_TOKEN_EXPIRES_MIN) -> str:
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET is not set")
    if not JWT_ALG:
        raise RuntimeError("JWT_ALG is not set")
    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError as e:
        raise ValueError("Invalid token") from e
