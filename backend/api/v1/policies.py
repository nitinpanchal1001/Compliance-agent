"""Policy listing + a retrieval (RAG) endpoint for testing the policy agent."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.policy_rag import retrieve_policies
from core.dependencies import CurrentUser
from db.base import get_db
from db.models.policy import Policy

router = APIRouter(prefix="/policies", tags=["policies"])


# ── Schemas ───────────────────────────────────────────

class PolicyResponse(BaseModel):
    id: str
    regulation: str
    title: str
    jurisdiction: str | None
    source: str | None
    clause_count: int
    is_active: bool
    scope: str  # "global" or "tenant"


class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    regulations: list[str] | None = None


class PolicyMatchResponse(BaseModel):
    regulation: str
    section: str
    citation: str
    text: str
    score: float


# ── Routes ────────────────────────────────────────────

@router.get("", response_model=list[PolicyResponse])
async def list_policies(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Global policies plus the caller's tenant-specific ones."""
    result = await db.execute(
        select(Policy)
        .where(
            or_(
                Policy.tenant_id.is_(None),
                Policy.tenant_id == current_user.tenant_id,
            )
        )
        .order_by(Policy.regulation)
    )
    return [
        PolicyResponse(
            id=p.id,
            regulation=p.regulation,
            title=p.title,
            jurisdiction=p.jurisdiction,
            source=p.source,
            clause_count=p.clause_count,
            is_active=p.is_active,
            scope="global" if p.tenant_id is None else "tenant",
        )
        for p in result.scalars().all()
    ]


@router.post("/search", response_model=list[PolicyMatchResponse])
async def search_policies(
    body: SearchRequest,
    current_user: CurrentUser,
):
    """Semantic retrieval over the policy corpus (global + tenant-owned)."""
    matches = retrieve_policies(
        tenant_id=current_user.tenant_id,
        query=body.query,
        top_k=body.top_k,
        regulations=body.regulations,
    )
    return [
        PolicyMatchResponse(
            regulation=m.regulation,
            section=m.section,
            citation=m.citation,
            text=m.text,
            score=m.score,
        )
        for m in matches
    ]
