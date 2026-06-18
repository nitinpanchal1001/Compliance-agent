"""Policy RAG agent — retrieves the policy clauses most relevant to a query.

This is the retrieval layer the reasoning agent (Phase 4) builds on. Given a
piece of document text, it embeds the query and returns the closest matching
regulatory clauses from the global corpus plus the tenant's own policies.
"""

from dataclasses import dataclass

from core import embeddings, vectorstore
from core.config import get_settings

settings = get_settings()


@dataclass
class PolicyMatch:
    regulation: str
    section: str
    citation: str
    text: str
    score: float

    @classmethod
    def from_payload(cls, p: dict) -> "PolicyMatch":
        return cls(
            regulation=p["regulation"],
            section=p["section"],
            citation=p["citation"],
            text=p["text"],
            score=p["score"],
        )


def retrieve_policies(
    tenant_id: str,
    query: str,
    top_k: int | None = None,
    regulations: list[str] | None = None,
) -> list[PolicyMatch]:
    """Embed `query` and return the top_k most relevant policy clauses.

    Searches the shared global corpus and this tenant's own policies, optionally
    filtered to specific regulations.
    """
    query = (query or "").strip()
    if not query:
        return []
    top_k = top_k or settings.policy_retrieval_top_k

    query_vector = embeddings.embed_text(query)
    hits = vectorstore.search_policies(
        tenant_id=tenant_id,
        query_vector=query_vector,
        limit=top_k,
        regulations=regulations,
    )
    return [PolicyMatch.from_payload(h) for h in hits]
