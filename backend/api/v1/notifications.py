"""Notification config + a test-send endpoint to verify delivery."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.dependencies import AdminUser, CurrentUser
from db.base import get_db
from db.models.tenant import Tenant
from workers.tasks.notifications import notify

router = APIRouter(prefix="/notifications", tags=["notifications"])
settings = get_settings()


class NotificationConfigResponse(BaseModel):
    enabled: bool
    email_enabled: bool
    email_recipients: list[str]
    events: list[str] | None  # None = all events
    smtp_configured: bool


class TestResponse(BaseModel):
    task_id: str
    detail: str


@router.get("/config", response_model=NotificationConfigResponse)
async def get_config(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Effective notification config for the caller's tenant."""
    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant not found")

    nconf = (tenant.settings or {}).get("notifications", {})
    return NotificationConfigResponse(
        enabled=nconf.get("enabled", settings.notifications_enabled),
        email_enabled=nconf.get("email_enabled", True),
        email_recipients=nconf.get("email_recipients", []),
        events=nconf.get("events"),
        smtp_configured=bool(settings.smtp_host),
    )


@router.post("/test", response_model=TestResponse, status_code=status.HTTP_202_ACCEPTED)
async def send_test(current_user: AdminUser):
    """Enqueue a test notification through the real dispatch pipeline (admin only)."""
    task = notify.delay(current_user.tenant_id, "test", {"by": current_user.email})
    return TestResponse(
        task_id=task.id,
        detail="Test notification enqueued; check the console channel (worker logs) "
        "and configured email recipients.",
    )
