from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class Policy(Base):
    """A regulation or internal policy whose clauses are embedded into Qdrant.

    tenant_id is NULL for the shared/global corpus (GDPR, HIPAA, ...) that every
    tenant checks against. A non-null tenant_id marks a tenant-specific policy.
    """

    __tablename__ = "policies"
    __table_args__ = (
        UniqueConstraint("tenant_id", "regulation", name="uq_policies_tenant_regulation"),
    )

    # NULL = global/shared corpus; otherwise owned by a specific tenant.
    tenant_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True
    )
    regulation: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    jurisdiction: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    clause_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        scope = self.tenant_id or "global"
        return f"<Policy regulation={self.regulation} scope={scope}>"
