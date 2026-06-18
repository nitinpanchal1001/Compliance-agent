"""Cases — trigger compliance analysis on a document and read the results."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.dependencies import CurrentUser, ReviewerUser
from db.base import get_db
from db.models.case import Case
from db.models.document import Document, DocumentStatus
from db.models.violation import Violation
from workers.tasks.analysis import analyze_case

router = APIRouter(prefix="/cases", tags=["cases"])


# ── Schemas ───────────────────────────────────────────

class CreateCaseRequest(BaseModel):
    document_id: str
    regulations: list[str] | None = None  # None = check the whole corpus


class ViolationResponse(BaseModel):
    id: str
    violation_type: str
    severity: str
    policy_ref: str
    doc_excerpt: str
    clause_text: str
    reasoning: str
    confidence: float

    @classmethod
    def from_model(cls, v: Violation) -> "ViolationResponse":
        return cls(
            id=v.id,
            violation_type=v.violation_type,
            severity=v.severity.value,
            policy_ref=v.policy_ref,
            doc_excerpt=v.doc_excerpt,
            clause_text=v.clause_text,
            reasoning=v.reasoning,
            confidence=v.confidence,
        )


class CaseResponse(BaseModel):
    id: str
    document_id: str
    status: str
    risk_score: int | None
    risk_tier: str | None
    regulations_checked: list
    violation_count: int
    created_at: datetime

    @classmethod
    def from_model(cls, c: Case, violation_count: int | None = None) -> "CaseResponse":
        return cls(
            id=c.id,
            document_id=c.document_id,
            status=c.status.value,
            risk_score=c.risk_score,
            risk_tier=c.risk_tier.value if c.risk_tier else None,
            regulations_checked=c.regulations_checked or [],
            violation_count=(
                violation_count
                if violation_count is not None
                else len(c.violations)
            ),
            created_at=c.created_at,
        )


class CaseDetailResponse(CaseResponse):
    report_json: dict | None
    violations: list[ViolationResponse]


# ── Routes ────────────────────────────────────────────

@router.post("", response_model=CaseResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_case(
    body: CreateCaseRequest,
    current_user: ReviewerUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # The document must exist in this tenant and be fully ingested.
    result = await db.execute(
        select(Document).where(
            Document.id == body.document_id,
            Document.tenant_id == current_user.tenant_id,
        )
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    if doc.status != DocumentStatus.ready:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Document is not ready for analysis (status={doc.status.value})",
        )

    case = Case(
        tenant_id=current_user.tenant_id,
        document_id=doc.id,
    )
    db.add(case)
    await db.flush()

    analyze_case.delay(case.id, body.regulations)

    return CaseResponse.from_model(case, violation_count=0)


@router.get("", response_model=list[CaseResponse])
async def list_cases(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Case)
        .where(Case.tenant_id == current_user.tenant_id)
        .options(selectinload(Case.violations))
        .order_by(Case.created_at.desc())
    )
    return [CaseResponse.from_model(c) for c in result.scalars().all()]


@router.get("/{case_id}", response_model=CaseDetailResponse)
async def get_case(
    case_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Case)
        .where(Case.id == case_id, Case.tenant_id == current_user.tenant_id)
        .options(selectinload(Case.violations))
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")

    base = CaseResponse.from_model(case)
    return CaseDetailResponse(
        **base.model_dump(),
        report_json=case.report_json,
        violations=[ViolationResponse.from_model(v) for v in case.violations],
    )
