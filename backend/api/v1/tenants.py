import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import audit
from core.dependencies import AdminUser, ClientIP, CurrentUser
from core.ratelimit import SignupRate
from core.security import hash_password
from core.validators import Email
from db.base import get_db
from db.models.tenant import Tenant
from db.models.user import User, UserRole

router = APIRouter(prefix="/tenants", tags=["tenants"])


# ── Schemas ───────────────────────────────────────────

class CreateTenantRequest(BaseModel):
    name: str
    slug: str
    admin_email: Email
    admin_password: str
    admin_full_name: str | None = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Slug must be lowercase alphanumeric with hyphens only")
        return v

    @field_validator("admin_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class TenantResponse(BaseModel):
    id: str
    name: str
    slug: str
    settings: dict
    is_active: bool


class UpdateTenantRequest(BaseModel):
    name: str | None = None
    settings: dict | None = None


# ── Routes ────────────────────────────────────────────

@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    body: CreateTenantRequest,
    ip: ClientIP,
    _rl: SignupRate,
    db: Annotated[AsyncSession, Depends(get_db)],
    # Note: this endpoint is intentionally open for the very first tenant bootstrap.
    # After that, protect it behind AdminUser in a super-admin setup if needed.
):
    existing = await db.execute(select(Tenant).where(Tenant.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant with slug '{body.slug}' already exists",
        )

    tenant = Tenant(name=body.name, slug=body.slug)
    db.add(tenant)
    await db.flush()  # get tenant.id before creating the user

    admin = User(
        tenant_id=tenant.id,
        email=body.admin_email,
        hashed_password=hash_password(body.admin_password),
        full_name=body.admin_full_name,
        role=UserRole.admin,
    )
    db.add(admin)
    await db.flush()

    await audit.record(
        db,
        tenant_id=tenant.id,
        user_id=admin.id,
        action="tenant.create",
        entity_type="tenant",
        entity_id=tenant.id,
        extra={"slug": tenant.slug},
        ip=ip,
    )

    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        settings=tenant.settings,
        is_active=tenant.is_active,
    )


@router.get("/me", response_model=TenantResponse)
async def get_my_tenant(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        settings=tenant.settings,
        is_active=tenant.is_active,
    )


@router.patch("/me", response_model=TenantResponse)
async def update_my_tenant(
    body: UpdateTenantRequest,
    current_user: AdminUser,
    ip: ClientIP,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    if body.name is not None:
        tenant.name = body.name
    if body.settings is not None:
        tenant.settings = {**tenant.settings, **body.settings}

    await audit.record(
        db,
        tenant_id=tenant.id,
        user_id=current_user.id,
        action="tenant.update",
        entity_type="tenant",
        entity_id=tenant.id,
        extra={"fields": [k for k in ("name", "settings") if getattr(body, k) is not None]},
        ip=ip,
    )

    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        settings=tenant.settings,
        is_active=tenant.is_active,
    )
