"""Audit logging — appends immutable records to the audit_logs table.

Records are added to the caller's session so they commit atomically with the
action they describe. The AuditLog model blocks updates at the ORM layer, so the
trail is append-only.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from db.models.audit_log import AuditLog


async def record(
    db: AsyncSession,
    *,
    tenant_id: str,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    user_id: str | None = None,
    extra: dict | None = None,
    ip: str | None = None,
) -> None:
    db.add(
        AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            extra_data=extra or {},
            ip_address=ip,
        )
    )
