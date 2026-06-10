"""Auth routes: login, register, refresh token."""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DBSession
from app.models.user import User, UserRole
from app.schemas.auth import Token, UserCreate, UserRead
from app.utils.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.utils.logging import get_logger

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: DBSession) -> UserRead:
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    try:
        role = UserRole(payload.role)
    except ValueError:
        role = UserRole.VIEWER

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=role,
        business_unit=payload.business_unit,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("user_registered", username=user.username, role=user.role)
    return user


@router.post("/login", response_model=Token)
async def login(email: str, password: str, db: DBSession) -> Token:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account inactive")

    access = create_access_token(str(user.id), user.role.value)
    refresh = create_refresh_token(str(user.id))
    logger.info("user_login", username=user.username)
    return Token(access_token=access, refresh_token=refresh)
