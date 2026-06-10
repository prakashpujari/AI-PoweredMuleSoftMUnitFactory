"""JWT auth, password hashing, RBAC helpers."""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings
from app.utils.exceptions import AuthenticationError, AuthorizationError

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

PERMISSION_MAP = {
    "admin": ["read", "write", "execute", "admin", "delete"],
    "architect": ["read", "write", "execute"],
    "developer": ["read", "write"],
    "qa": ["read", "execute"],
    "viewer": ["read"],
}


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, role: str, extra: Optional[dict] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as e:
        raise AuthenticationError(f"Invalid token: {e}")


def require_permission(role: str, permission: str) -> None:
    allowed = PERMISSION_MAP.get(role, [])
    if permission not in allowed:
        raise AuthorizationError(
            f"Role '{role}' lacks permission '{permission}'"
        )
