import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from db.models.case import Case


class ReviewDecision(enum.StrEnum):
    confirmed = "confirmed"
    dismissed = "dismissed"
    escalated = "escalated"


class HumanReview(Base):
    __tablename__ = "human_reviews"

    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # NULL for a case-level decision (e.g. escalation); set for a per-violation review.
    violation_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("violations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reviewer_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    decision: Mapped[ReviewDecision] = mapped_column(
        Enum(ReviewDecision, name="review_decision"), nullable=False
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    case: Mapped["Case"] = relationship("Case", back_populates="human_reviews", lazy="noload")

    def __repr__(self) -> str:
        return f"<HumanReview case={self.case_id} decision={self.decision}>"
