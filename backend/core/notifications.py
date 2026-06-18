"""Notification senders + message formatting.

Channels:
  - console: always available; logs the formatted message (dev + demo).
  - email:   SMTP, using global creds; raises NotConfigured if SMTP isn't set.

The dispatch/routing logic (which tenant, which channels, recipients) lives in
the Celery task; this module just formats and sends.
"""

import json
import smtplib
from email.message import EmailMessage

import structlog

from core.config import get_settings

settings = get_settings()
log = structlog.get_logger()


class NotConfigured(Exception):
    """Raised when a channel is selected but its transport isn't configured."""


def format_event(event_type: str, ctx: dict) -> tuple[str, str]:
    """Return (subject, body) for an event type + context dict."""
    if event_type == "case_analyzed":
        tier = ctx.get("risk_tier") or "unknown"
        alert = "🚨 " if tier in ("high", "critical") else ""
        subject = (
            f"{alert}Compliance case analyzed — {tier} risk "
            f"({ctx.get('violation_count', 0)} violations)"
        )
        body = (
            f"A document analysis has completed.\n\n"
            f"Case:        {ctx.get('case_id')}\n"
            f"Document:    {ctx.get('document_name', ctx.get('document_id'))}\n"
            f"Risk score:  {ctx.get('risk_score')}/100 ({tier})\n"
            f"Violations:  {ctx.get('violation_count', 0)}\n"
            f"Status:      {ctx.get('status')}\n"
        )
    elif event_type == "case_escalated":
        subject = "⚠️ Compliance case escalated for senior review"
        body = (
            f"A case has been escalated.\n\n"
            f"Case:  {ctx.get('case_id')}\n"
            f"By:    {ctx.get('reviewer_email', ctx.get('reviewer_id'))}\n"
            f"Note:  {ctx.get('note') or '(none)'}\n"
        )
    elif event_type == "case_closed":
        subject = "✅ Compliance case closed"
        body = (
            f"A case has been fully reviewed and closed.\n\n"
            f"Case:        {ctx.get('case_id')}\n"
            f"Final risk:  {ctx.get('risk_score')}/100 ({ctx.get('risk_tier')})\n"
        )
    elif event_type == "test":
        subject = "🔔 Test notification from Compliance Agent"
        body = "This is a test notification. If you received it, delivery works."
    else:
        subject = f"Compliance notification: {event_type}"
        body = json.dumps(ctx, indent=2, default=str)
    return subject, body


def send_console(event_type: str, subject: str, body: str) -> None:
    """Always-available channel: emit the notification to the structured log."""
    log.info(
        "notification.console", event_kind=event_type, subject=subject, body=body
    )


def send_email(recipients: list[str], subject: str, body: str) -> None:
    """Send via the globally configured SMTP server. Raises NotConfigured if unset."""
    if not settings.smtp_host:
        raise NotConfigured("SMTP host is not configured")
    if not recipients:
        raise NotConfigured("no email recipients")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.notify_from_email
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
        server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
