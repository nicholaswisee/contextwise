"""Owner-protected document ingestion and provenance routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from pydantic import BaseModel

from contextwise.api.dependencies import get_ingestion_service, require_owner
from contextwise.application.ingestion.service import IngestionService, UploadError
from contextwise.infrastructure.models import (
    Document,
    DocumentSegment,
    DocumentVersion,
    IngestionJob,
)

router = APIRouter(prefix="/v1", tags=["documents"])


class DocumentView(BaseModel):
    id: str
    filename: str


class VersionView(BaseModel):
    id: str
    document_id: str
    number: int
    sha256: str
    mime_type: str
    size_bytes: int
    status: str
    error_code: str | None


class SegmentView(BaseModel):
    id: str
    ordinal: int
    text: str
    page: int | None
    section: str | None
    start_offset: int
    end_offset: int


class JobView(BaseModel):
    id: str
    version_id: str
    status: str
    attempts: int
    error_code: str | None
    trace_id: str


class UploadView(BaseModel):
    document: DocumentView
    version: VersionView
    job: JobView
    duplicate: bool


class DocumentDetail(DocumentView):
    versions: list[VersionView]


class VersionDetail(VersionView):
    segments: list[SegmentView]
    job: JobView | None
    extracted_text: str | None


def _document(row: Document) -> DocumentView:
    return DocumentView(id=row.id, filename=row.filename)


def _version(row: DocumentVersion) -> VersionView:
    return VersionView(
        id=row.id,
        document_id=row.document_id,
        number=row.number,
        sha256=row.sha256,
        mime_type=row.mime_type,
        size_bytes=row.size_bytes,
        status=row.status,
        error_code=row.error_code,
    )


def _job(row: IngestionJob) -> JobView:
    return JobView(
        id=row.id,
        version_id=row.version_id,
        status=row.status,
        attempts=row.attempts,
        error_code=row.error_code,
        trace_id=row.trace_id,
    )


def _segment(row: DocumentSegment) -> SegmentView:
    return SegmentView(
        id=row.id,
        ordinal=row.ordinal,
        text=row.text,
        page=row.page,
        section=row.section,
        start_offset=row.start_offset,
        end_offset=row.end_offset,
    )


@router.post("/documents", response_model=UploadView, status_code=202)
async def upload_document(
    file: UploadFile,
    request: Request,
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> UploadView:
    data = await file.read(service.max_bytes + 1)
    try:
        result = await service.upload(
            owner_id, file.filename or "", file.content_type, data, request.state.request_id
        )
    except UploadError as error:
        raise HTTPException(status_code=422, detail=error.code) from error
    return UploadView(
        document=_document(result.document),
        version=_version(result.version),
        job=_job(result.job),
        duplicate=result.duplicate,
    )


@router.get("/documents", response_model=list[DocumentView])
async def list_documents(
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> list[DocumentView]:
    return [_document(row) for row in await service.list_documents(owner_id)]


@router.get("/documents/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: str,
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> DocumentDetail:
    document = await service.get_document(document_id, owner_id)
    if document is None:
        raise HTTPException(status_code=404, detail="document_not_found")
    versions = await service.list_versions(document_id, owner_id)
    return DocumentDetail(
        **_document(document).model_dump(), versions=[_version(row) for row in versions]
    )


@router.get("/document-versions/{version_id}", response_model=VersionDetail)
async def get_document_version(
    version_id: str,
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> VersionDetail:
    detail = await service.get_version(version_id, owner_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="version_not_found")
    version, segments, job = detail
    return VersionDetail(
        **_version(version).model_dump(),
        segments=[_segment(row) for row in segments],
        job=_job(job) if job else None,
        extracted_text=version.extracted_text,
    )


@router.get("/ingestion-jobs/{job_id}", response_model=JobView)
async def get_ingestion_job(
    job_id: str,
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> JobView:
    job = await service.get_job(job_id, owner_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    return _job(job)


@router.post("/ingestion-jobs/{job_id}/retry", response_model=JobView, status_code=202)
async def retry_ingestion_job(
    job_id: str,
    request: Request,
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> JobView:
    job = await service.retry(job_id, owner_id, request.state.request_id)
    if job is None:
        raise HTTPException(status_code=409, detail="job_not_retryable")
    return _job(job)


@router.post("/document-versions/{version_id}/reprocess", response_model=JobView, status_code=202)
async def reprocess_document_version(
    version_id: str,
    request: Request,
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> JobView:
    job = await service.reprocess(version_id, owner_id, request.state.request_id)
    if job is None:
        raise HTTPException(status_code=409, detail="version_not_reprocessable")
    return _job(job)


@router.post("/ingestion-jobs/{job_id}/cancel", response_model=JobView)
async def cancel_ingestion_job(
    job_id: str,
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> JobView:
    job = await service.cancel(job_id, owner_id)
    if job is None:
        raise HTTPException(status_code=409, detail="job_not_cancellable")
    return _job(job)
