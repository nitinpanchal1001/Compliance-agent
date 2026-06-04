import enum

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class CaseStatus(str, enum.Enum):
    open = "open"
    pending_review = "pending_review"
    closed = "closed"


class RiskTier(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class Case(Base):
    __tablename__ = "cases"

    tenant_id: Mapped[str] = mapped_column(
        String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[str] = mapped_column(
        String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, name="case_status"),
        default=CaseStatus.open,
        nullable=False,
        index=True,
    )
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_tier: Mapped[RiskTier | None] = mapped_column(
        Enum(RiskTier, name="risk_tier"), nullable=True, index=True
    )
    regulations_checked: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    report_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    violations: Mapped[list["Violation"]] = relationship(  # noqa: F821
        "Violation", back_populates="case", lazy="noload", cascade="all, delete-orphan"
    )
    human_reviews: Mapped[list["HumanReview"]] = relationship(  # noqa: F821
        "HumanReview", back_populates="case", lazy="noload", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Case id={self.id} risk_tier={self.risk_tier}>"


from db.models.human_review import HumanReview  # noqa: E402, F401
from db.models.violation import Violation  # noqa: E402, F401
