"""Importing this package registers every model in SQLAlchemy's mapper registry.

This matters for any process that touches a single model in isolation (e.g. the
Celery worker loading only Document) — without the related models imported,
SQLAlchemy can't resolve cross-table foreign keys.
"""

from db.models.audit_log import AuditLog
from db.models.case import Case
from db.models.document import Document
from db.models.human_review import HumanReview
from db.models.tenant import Tenant
from db.models.user import User
from db.models.violation import Violation

__all__ = [
    "AuditLog",
    "Case",
    "Document",
    "HumanReview",
    "Tenant",
    "User",
    "Violation",
]
