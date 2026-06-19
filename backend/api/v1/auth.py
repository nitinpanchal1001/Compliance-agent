from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import audit, token_store
from core.dependencies import ClientIP, CurrentUser
from core.ratelimit import LoginRate, RefreshRate
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from core.validators import Email
from db.base import get_db
from db.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Request / Response schemas ────────────────────────

class LoginRequest(BaseModel):
    email: Email
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class MeResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str
    tenant_id: str


# ── Routes ────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    ip: ClientIP,
    _rl: LoginRate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    user.last_login = datetime.now(UTC)

    access_token = create_access_token(user.id, user.tenant_id, user.role.value)
    refresh_token, jti = create_refresh_token(user.id, user.tenant_id)
    await token_store.save(jti, user.id)
    await audit.record(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        action="auth.login",
        entity_type="user",
        entity_id=user.id,
        ip=ip,
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    _rl: RefreshRate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise JWTError
        user_id: str = payload["sub"]
        jti: str = payload["jti"]
    except (JWTError, KeyError):
        raise invalid

    # The jti must still be registered (not rotated away or revoked).
    if not await token_store.is_valid(jti):
        raise invalid

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise invalid

    # Rotate: kill the presented token, issue a fresh pair.
    await token_store.revoke(jti, user_id)
    access_token = create_access_token(user.id, user.tenant_id, user.role.value)
    new_refresh, new_jti = create_refresh_token(user.id, user.tenant_id)
    await token_store.save(new_jti, user.id)
    return TokenResponse(access_token=access_token, refresh_token=new_refresh)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest):
    """Revoke a single refresh token (this session). Idempotent."""
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") == "refresh" and "jti" in payload:
            await token_store.revoke(payload["jti"], payload.get("sub"))
    except JWTError:
        pass  # already invalid/expired — nothing to revoke


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(current_user: CurrentUser):
    """Revoke every refresh token for the current user (all sessions)."""
    await token_store.revoke_all(current_user.id)


@router.get("/me", response_model=MeResponse)
async def me(current_user: CurrentUser):
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        tenant_id=current_user.tenant_id,
    )
