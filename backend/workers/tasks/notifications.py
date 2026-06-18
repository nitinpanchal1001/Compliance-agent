"""Notification dispatch task.

Resolves a tenant's notification config (tenant.settings.notifications, with
global .env fallback), picks the enabled channels + recipients, and sends. Each
channel is best-effort: one channel failing never fails the others.

Per-tenant config shape (in tenant.settings):
    {
      "notifications": {
        "enabled": true,
        "email_enabled": true,
        "email_recipients": ["compliance@acme.com"],
        "events": ["case_analyzed", "case_escalated", "case_closed"]  // optional filter
      }
    }
"""

import structlog
from sqlalchemy import select

from core import notifications
from core.config import get_settings
from db.models.tenant import Tenant
from db.models.user import User, UserRole
from workers.celery_app import celery_app
from workers.db import get_sync_db

settings = get_settings()
log = structlog.get_logger()


@celery_app.task(
    bind=True,
    name="workers.tasks.notifications.notify",
    max_retries=2,
    default_retry_delay=30,
)
def notify(self, tenant_id: str, event_type: str, context: dict) -> dict:
    # 1. Resolve tenant + config.
    with get_sync_db() as db:
        tenant = db.get(Tenant, tenant_id)
        if tenant is None:
            return {"status": "no_tenant", "tenant_id": tenant_id}

        nconf = (tenant.settings or {}).get("notifications", {})
        if not nconf.get("enabled", settings.notifications_enabled):
            return {"status": "disabled"}

        allowed_events = nconf.get("events")
        if allowed_events is not None and event_type not in allowed_events:
            return {"status": "skipped_event", "event": event_type}

        email_enabled = nconf.get("email_enabled", True)
        recipients = nconf.get("email_recipients") or []
        if not recipients:
            # Fall back to active admins/reviewers in the tenant.
            rows = db.execute(
                select(User.email).where(
                    User.tenant_id == tenant_id,
                    User.role.in_([UserRole.admin, UserRole.reviewer]),
                    User.is_active.is_(True),
                )
            ).scalars().all()
            recipients = list(rows)

    # 2. Format once.
    subject, body = notifications.format_event(event_type, context)

    # 3. Dispatch per channel (best-effort).
    results: dict[str, str] = {}

    notifications.send_console(event_type, subject, body)
    results["console"] = "sent"

    if email_enabled:
        try:
            notifications.send_email(recipients, subject, body)
            results["email"] = f"sent to {len(recipients)} recipient(s)"
        except notifications.NotConfigured as e:
            results["email"] = f"skipped: {e}"
        except Exception as e:  # noqa: BLE001 — never let one channel kill the task
            log.error("notification.email_failed", error=str(e), tenant_id=tenant_id)
            results["email"] = f"error: {e}"
    else:
        results["email"] = "disabled"

    log.info(
        "notification.dispatched",
        event_kind=event_type,
        tenant_id=tenant_id,
        results=results,
    )
    return {"status": "dispatched", "event": event_type, "results": results}
