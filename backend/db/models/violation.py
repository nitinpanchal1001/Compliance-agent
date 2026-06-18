import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from db.models.case import Case


class ViolationSeverity(enum.StrEnum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class ViolationReviewStatus(enum.StrEnum):
    pending = "pending"      # awaiting human review
    confirmed = "confirmed"  # reviewer agrees it's a real violation
    dismissed = "dismissed"  # reviewer marks it a false positive


class Violation(Base):
    __tablename__ = "violations"

    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    violation_type: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[ViolationSeverity] = mapped_column(
        Enum(ViolationSeverity, name="violation_severity"), nullable=False, index=True
    )
    policy_ref: Mapped[str] = mapped_column(String(500), nullable=False)
    doc_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    clause_text: Mapped[str] = mapped_column(Text, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # ── Human review (Phase 6) ──
    review_status: Mapped[ViolationReviewStatus] = mapped_column(
        Enum(ViolationReviewStatus, name="violation_review_status"),
        default=ViolationReviewStatus.pending,
        nullable=False,
        index=True,
    )
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(
        String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    case: Mapped["Case"] = relationship("Case", back_populates="violations", lazy="noload")

    def __repr__(self) -> str:
        return f"<Violation type={self.violation_type} severity={self.severity}>"
