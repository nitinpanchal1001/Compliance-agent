"""Document ingestion task: S3 → parse → chunk → embed → Qdrant.

Lifecycle of Document.status across this task:
    pending → processing → ready   (success)
                         → failed  (on any error, with error_message)
"""

import structlog

from core import embeddings, storage, vectorstore
from db.models.document import Document, DocumentStatus
from workers.celery_app import celery_app
from workers.chunking import chunk_text
from workers.db import get_sync_db
from workers.parsers import extract_text

log = structlog.get_logger()


@celery_app.task(
    bind=True,
    name="workers.tasks.ingestion.ingest_document",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def ingest_document(self, document_id: str) -> dict:
    # 1. Load the document and mark it processing.
    with get_sync_db() as db:
        doc = db.get(Document, document_id)
        if doc is None:
            log.warning("ingest.document_missing", document_id=document_id)
            return {"status": "missing", "document_id": document_id}
        tenant_id = doc.tenant_id
        s3_key = doc.s3_key
        name = doc.name
        file_type = doc.file_type
        doc.status = DocumentStatus.processing
        doc.error_message = None

    try:
        # 2. Pull the raw bytes from S3.
        raw = storage.download_bytes(s3_key)

        # 3. Extract text (and page count for PDFs).
        full_text, page_count = extract_text(file_type, raw, name)
        if not full_text.strip():
            raise ValueError("No extractable text found in document")

        # 4. Chunk + embed.
        chunks = chunk_text(full_text)
        vectors = embeddings.embed_texts(chunks)

        # 5. Upsert into Qdrant (tenant-scoped payload).
        vectorstore.ensure_collection()
        vectorstore.delete_document(document_id)  # clear stale chunks on re-ingest
        vectorstore.upsert_chunks(
            tenant_id=tenant_id,
            document_id=document_id,
            chunks=list(zip(range(len(chunks)), chunks, vectors)),
        )

        # 6. Mark ready.
        with get_sync_db() as db:
            doc = db.get(Document, document_id)
            doc.status = DocumentStatus.ready
            doc.page_count = page_count
            doc.error_message = None

        log.info(
            "ingest.success",
            document_id=document_id,
            chunks=len(chunks),
            page_count=page_count,
        )
        return {
            "status": "ready",
            "document_id": document_id,
            "chunks": len(chunks),
        }

    except Exception as exc:
        log.error("ingest.failed", document_id=document_id, error=str(exc))
        with get_sync_db() as db:
            doc = db.get(Document, document_id)
            if doc is not None:
                doc.status = DocumentStatus.failed
                doc.error_message = str(exc)[:1000]
        # Retry transient failures (network/S3/OpenAI); gives up after max_retries.
        raise self.retry(exc=exc)
