from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.core.config import AppMode, settings
from pulseroute.core.database import get_db
from pulseroute.core.security import create_access_token, hash_password, verify_password
from pulseroute.models.user import User
from pulseroute.schemas.auth import LoginRequest, Token, UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    if settings.APP_MODE == AppMode.PRIVATE and not settings.ALLOW_PUBLIC_REGISTRATION:
        # Check if any user exists. If not, allow first root admin creation
        count_res = await db.execute(select(User))
        if count_res.first() is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Public registration is disabled in Private mode."
            )

    existing = await db.execute(select(User).where(User.email == user_in.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered.")

    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        is_superuser=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    token = create_access_token(data={"sub": str(user.id), "email": user.email}, expires_delta=timedelta(days=7))
    return {"access_token": token, "token_type": "bearer"}
