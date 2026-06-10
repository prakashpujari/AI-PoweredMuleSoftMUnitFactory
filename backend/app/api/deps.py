"""FastAPI dependency injectors: DB session, current user, permissions."""
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.security import decode_token, require_permission

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_payload(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)]
) -> dict:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return decode_token(credentials.credentials)


async def require_read(payload: Annotated[dict, Depends(get_current_user_payload)]) -> dict:
    require_permission(payload.get("role", "viewer"), "read")
    return payload


async def require_write(payload: Annotated[dict, Depends(get_current_user_payload)]) -> dict:
    require_permission(payload.get("role", "viewer"), "write")
    return payload


async def require_execute(payload: Annotated[dict, Depends(get_current_user_payload)]) -> dict:
    require_permission(payload.get("role", "viewer"), "execute")
    return payload


async def require_admin(payload: Annotated[dict, Depends(get_current_user_payload)]) -> dict:
    require_permission(payload.get("role", "viewer"), "admin")
    return payload


DBSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[dict, Depends(get_current_user_payload)]
ReadUser = Annotated[dict, Depends(require_read)]
WriteUser = Annotated[dict, Depends(require_write)]
ExecuteUser = Annotated[dict, Depends(require_execute)]
