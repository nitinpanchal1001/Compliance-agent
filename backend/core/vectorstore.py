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
