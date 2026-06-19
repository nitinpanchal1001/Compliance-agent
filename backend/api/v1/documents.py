"""Document upload + retrieval. Upload stores the raw file in S3, creates a
Document row, and enqueues the async ingestion task."""

from datetime import datetime
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import audit, storage
from core.config import get_settings
from core.dependencies import ClientIP, CurrentUser, ReviewerUser
from db.base import get_db
from db.models.document import Document, DocumentFileType, DocumentStatus
from workers.tasks.ingestion import ingest_document

router = APIRouter(prefix="/documents", tags=["documents"])
settings = get_settings()


# ── File type inference ───────────────────────────────

_EXT_TO_TYPE: dict[str, DocumentFileType] = {
    ".pdf": DocumentFileType.pdf,
    ".txt": DocumentFileType.text,
    ".md": DocumentFileType.text,
    ".eml": DocumentFileType.email,
    ".json": DocumentFileType.slack,
    ".mp3": DocumentFileType.audio,
    ".wav": DocumentFileType.audio,
    ".m4a": DocumentFileType.audio,
    ".mp4": DocumentFileType.audio,
}


def _infer_file_type(filename: str) -> DocumentFileType:
    return _EXT_TO_TYPE.get(Path(filename).suffix.lower(), DocumentFileType.other)


# ── Schemas ───────────────────────────────────────────

class DocumentResponse(BaseModel):
    id: str
    name: str
    file_type: str
    status: str
    size_bytes: int | None
    page_count: int | None
    error_message: str | None
    uploaded_by: str | None
    created_at: datetime

    @classmethod
    def from_model(cls, d: Document) -> "DocumentResponse":
        return cls(
            id=d.id,
            name=d.name,
            file_type=d.file_type.value,
            status=d.status.value,
            size_bytes=d.size_bytes,
            page_count=d.page_count,
            error_message=d.error_message,
            uploaded_by=d.uploaded_by,
            created_at=d.created_at,
        )


class DownloadResponse(BaseModel):
    url: str
    expires_seconds: int


# ── Routes ────────────────────────────────────────────

@router.post("", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    current_user: ReviewerUser,
    ip: ClientIP,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
    file_type: Annotated[DocumentFileType | None, Form()] = None,
):
    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty file")
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"File exceeds {settings.max_upload_mb} MB limit",
        )

    filename = file.filename or "upload"
    resolved_type = file_type or _infer_file_type(filename)

    # Tenant-scoped S3 key so objects are naturally partitioned per tenant.
    s3_key = f"{current_user.tenant_id}/{uuid4()}/{filename}"
    storage.upload_bytes(data, s3_key, content_type=file.content_type)

    doc = Document(
        tenant_id=current_user.tenant_id,
        uploaded_by=current_user.id,
        name=filename,
        s3_key=s3_key,
        file_type=resolved_type,
        size_bytes=len(data),
        status=DocumentStatus.pending,
    )
    db.add(doc)
    await db.flush()  # assign doc.id before enqueueing

    # Enqueue async ingestion (runs in the Celery worker).
    ingest_document.delay(doc.id)

    await audit.record(
        db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="document.upload",
        entity_type="document",
        entity_id=doc.id,
        extra={"name": doc.name, "file_type": doc.file_type.value},
        ip=ip,
    )

    return DocumentResponse.from_model(doc)


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    result = await db.execute(
        select(Document)
        .where(Document.tenant_id == current_user.tenant_id)
        .order_by(Document.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [DocumentResponse.from_model(d) for d in result.scalars().all()]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    doc = await _get_owned_document(document_id, current_user.tenant_id, db)
    return DocumentResponse.from_model(doc)


@router.get("/{document_id}/download", response_model=DownloadResponse)
async def download_document(
    document_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    doc = await _get_owned_document(document_id, current_user.tenant_id, db)
    url = storage.generate_presigned_url(doc.s3_key)
    return DownloadResponse(url=url, expires_seconds=3600)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: ReviewerUser,
    ip: ClientIP,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    doc = await _get_owned_document(document_id, current_user.tenant_id, db)
    # Best-effort cleanup of the raw object; row + cascade handle the rest.
    storage.delete_object(doc.s3_key)
    await audit.record(
        db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="document.delete",
        entity_type="document",
        entity_id=doc.id,
        extra={"name": doc.name},
        ip=ip,
    )
    await db.delete(doc)


# ── Helpers ───────────────────────────────────────────

async def _get_owned_document(
    document_id: str, tenant_id: str, db: AsyncSession
) -> Document:
    result = await db.execute(
        select(Document).where(
            Document.id == document_id, Document.tenant_id == tenant_id
        )
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return doc
