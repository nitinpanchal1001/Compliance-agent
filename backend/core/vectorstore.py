"""Qdrant vector store — one shared collection, tenant isolation via payload filter.

Every chunk is stored in the `document_chunks` collection with a payload carrying
`tenant_id` and `document_id`. All reads MUST filter by tenant_id so one tenant can
never retrieve another tenant's vectors.
"""

from functools import lru_cache
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models

from core.config import get_settings

settings = get_settings()

COLLECTION = settings.qdrant_collection


@lru_cache
def get_client() -> QdrantClient:
    return QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        api_key=settings.qdrant_api_key or None,
    )


def _point_id(document_id: str, chunk_index: int) -> str:
    """Deterministic ID so re-ingesting a document overwrites its old chunks."""
    return str(uuid5(NAMESPACE_URL, f"{document_id}:{chunk_index}"))


def ensure_collection() -> None:
    """Create the collection + payload indexes if they don't exist (idempotent)."""
    client = get_client()
    if client.collection_exists(COLLECTION):
        return
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=models.VectorParams(
            size=settings.embedding_dim, distance=models.Distance.COSINE
        ),
    )
    # Indexed payload fields make tenant/document filtering fast.
    for field in ("tenant_id", "document_id"):
        client.create_payload_index(
            collection_name=COLLECTION,
            field_name=field,
            field_schema=models.PayloadSchemaType.KEYWORD,
        )


def upsert_chunks(
    tenant_id: str, document_id: str, chunks: list[tuple[int, str, list[float]]]
) -> None:
    """chunks: list of (chunk_index, text, vector)."""
    points = [
        models.PointStruct(
            id=_point_id(document_id, idx),
            vector=vector,
            payload={
                "tenant_id": tenant_id,
                "document_id": document_id,
                "chunk_index": idx,
                "text": text,
            },
        )
        for idx, text, vector in chunks
    ]
    if points:
        get_client().upsert(collection_name=COLLECTION, points=points)


def delete_document(document_id: str) -> None:
    get_client().delete(
        collection_name=COLLECTION,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=document_id),
                    )
                ]
            )
        ),
    )


def search(
    tenant_id: str,
    query_vector: list[float],
    limit: int = 5,
    document_id: str | None = None,
) -> list[dict]:
    """Tenant-scoped similarity search. Returns payloads with a `score`."""
    must = [
        models.FieldCondition(
            key="tenant_id", match=models.MatchValue(value=tenant_id)
        )
    ]
    if document_id:
        must.append(
            models.FieldCondition(
                key="document_id", match=models.MatchValue(value=document_id)
            )
        )
    hits = get_client().query_points(
        collection_name=COLLECTION,
        query=query_vector,
        query_filter=models.Filter(must=must),
        limit=limit,
        with_payload=True,
    ).points
    return [{**h.payload, "score": h.score} for h in hits]


# ── Policy corpus collection ──────────────────────────
# Separate collection for reference regulations. Each point's payload carries an
# `owner` field: "global" for the shared corpus, or a tenant_id for tenant-owned
# policies. Retrieval returns global policies plus the caller's own.

POLICY_COLLECTION = settings.policy_collection


def _policy_point_id(policy_id: str, section: str, chunk_index: int) -> str:
    """Deterministic ID so re-seeding a policy overwrites its old clauses."""
    return str(uuid5(NAMESPACE_URL, f"policy:{policy_id}:{section}:{chunk_index}"))


def ensure_policy_collection() -> None:
    client = get_client()
    if client.collection_exists(POLICY_COLLECTION):
        return
    client.create_collection(
        collection_name=POLICY_COLLECTION,
        vectors_config=models.VectorParams(
            size=settings.embedding_dim, distance=models.Distance.COSINE
        ),
    )
    for field in ("owner", "regulation", "policy_id"):
        client.create_payload_index(
            collection_name=POLICY_COLLECTION,
            field_name=field,
            field_schema=models.PayloadSchemaType.KEYWORD,
        )


def delete_policy(policy_id: str) -> None:
    get_client().delete(
        collection_name=POLICY_COLLECTION,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="policy_id", match=models.MatchValue(value=policy_id)
                    )
                ]
            )
        ),
    )


def upsert_policy_chunks(points: list[dict]) -> None:
    """points: list of dicts with keys
    policy_id, owner, regulation, section, citation, chunk_index, text, vector.
    """
    structs = [
        models.PointStruct(
            id=_policy_point_id(p["policy_id"], p["section"], p["chunk_index"]),
            vector=p["vector"],
            payload={
                "owner": p["owner"],
                "policy_id": p["policy_id"],
                "regulation": p["regulation"],
                "section": p["section"],
                "citation": p["citation"],
                "chunk_index": p["chunk_index"],
                "text": p["text"],
            },
        )
        for p in points
    ]
    if structs:
        get_client().upsert(collection_name=POLICY_COLLECTION, points=structs)


def search_policies(
    tenant_id: str,
    query_vector: list[float],
    limit: int = 5,
    regulations: list[str] | None = None,
) -> list[dict]:
    """Retrieve clauses from the global corpus AND the caller's own policies.

    Optionally narrow to specific regulations (e.g. ["GDPR", "HIPAA"]).
    """
    # owner is "global" OR the caller's tenant_id
    must: list = [
        models.Filter(
            should=[
                models.FieldCondition(
                    key="owner", match=models.MatchValue(value="global")
                ),
                models.FieldCondition(
                    key="owner", match=models.MatchValue(value=tenant_id)
                ),
            ]
        )
    ]
    if regulations:
        must.append(
            models.FieldCondition(
                key="regulation", match=models.MatchAny(any=regulations)
            )
        )
    hits = get_client().query_points(
        collection_name=POLICY_COLLECTION,
        query=query_vector,
        query_filter=models.Filter(must=must),
        limit=limit,
        with_payload=True,
    ).points
    return [{**h.payload, "score": h.score} for h in hits]
