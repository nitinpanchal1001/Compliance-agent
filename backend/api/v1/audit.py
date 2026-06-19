"""Audit log — read-only, admin-only, paginated view of the immutable trail."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import AdminUser
from db.base import get_db
from db.models.audit_log import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditEntry(BaseModel):
    id: str
    action: str
    entity_type: str
    entity_id: str | None
    user_id: str | None
    extra_data: dict
    ip_address: str | None
    created_at: datetime


@router.get("", response_model=list[AuditEntry])
async def list_audit(
    current_user: AdminUser,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    action: str | None = None,
):
    where = [AuditLog.tenant_id == current_user.tenant_id]
    if action:
        where.append(AuditLog.action == action)

    total = await db.scalar(
        select(func.count()).select_from(AuditLog).where(*where)
    )
    response.headers["X-Total-Count"] = str(total or 0)

    result = await db.execute(
        select(AuditLog)
        .where(*where)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [
        AuditEntry(
            id=a.id,
            action=a.action,
            entity_type=a.entity_type,
            entity_id=a.entity_id,
            user_id=a.user_id,
            extra_data=a.extra_data,
            ip_address=a.ip_address,
            created_at=a.created_at,
        )
        for a in result.scalars().all()
    ]
