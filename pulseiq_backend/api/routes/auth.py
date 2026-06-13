from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseiq_backend.core.config import settings
from pulseiq_backend.core.database import get_db
from pulseiq_backend.core.security import (
    ROLE_SUPER_ADMIN,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from pulseiq_backend.models.user import User
from pulseiq_backend.schemas.user import ResetPasswordRequest, SuperAdminBootstrapRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/bootstrap-super-admin", response_model=TokenResponse, status_code=201)
async def bootstrap_super_admin(body: SuperAdminBootstrapRequest, db: AsyncSession = Depends(get_db)):
    if not settings.super_admin_setup_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Super admin bootstrap is not configured",
        )

    if body.setup_token != settings.super_admin_setup_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid setup token")

    if len(body.password) < 12:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Password must be at least 12 characters")

    existing_super_admin = await db.execute(select(User).where(User.role == ROLE_SUPER_ADMIN))
    if existing_super_admin.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Super admin already exists")

    existing_email = await db.execute(select(User).where(User.email == body.email))
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        tenant_id=None,
        email=body.email,
        hashed_password=hash_password(body.password),
        role=ROLE_SUPER_ADMIN,
        is_active=True,
        must_reset_password=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id, user.role, user.tenant_id)
    return TokenResponse(access_token=token, must_reset_password=user.must_reset_password)


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form.username))
    user = result.scalar_one_or_none()

    if not user or not user.is_active or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user.id, user.role, user.tenant_id)
    return TokenResponse(access_token=token, must_reset_password=user.must_reset_password)


@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    if body.current_password == body.new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must differ from current")

    current_user.hashed_password = hash_password(body.new_password)
    current_user.must_reset_password = False
    current_user.password_reset_token = None
    await db.commit()
    return {"message": "Password updated successfully"}
