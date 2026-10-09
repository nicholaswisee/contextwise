"""Upload validation, owner-scoped document access, and the durable worker."""

import asyncio
import logging
from contextlib import suppress
from dataclasses import dataclass
from pathlib import PurePath

from contextwise.application.ingestion.parsers import ParseError, extract
from contextwise.infrastructure.documents import DocumentRepository
from contextwise.infrastructure.models import (
    Document,
    DocumentSegment,
    DocumentVersion,
    IngestionJob,
)
from contextwise.infrastructure.object_store import LocalObjectStore

logger = logging.getLogger(__name__)


class UploadError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class UploadResult:
    document: Document
    version: DocumentVersion
    job: IngestionJob
    duplicate: bool


class IngestionService:
    def __init__(
        self,
        repository: DocumentRepository,
        store: LocalObjectStore,
        max_bytes: int,
        timeout_seconds: float,
    ):
        self.repository = repository
        self.store = store
        self.max_bytes = max_bytes
        self.timeout_seconds = timeout_seconds
        self._worker: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._worker is None:
            self._worker = asyncio.create_task(self._run(), name="contextwise-ingestion")

    async def stop(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
            with suppress(asyncio.CancelledError):
                await self._worker
            self._worker = None

    async def upload(
        self,
        owner_id: str,
        filename: str,
        content_type: str | None,
        data: bytes,
        trace_id: str,
    ) -> UploadResult:
        mime_type = self._validate(filename, content_type, data)
        digest = await asyncio.to_thread(self.store.put, data)
        document, version, job, duplicate = await self.repository.add_upload(
            owner_id, filename, mime_type, len(data), digest, trace_id
        )
        return UploadResult(document, version, job, duplicate)

    def _validate(self, filename: str, content_type: str | None, data: bytes) -> str:
        if (
            not filename
            or filename != PurePath(filename).name
            or "\\" in filename
            or len(filename) > 255
            or any(ord(character) < 32 or ord(character) == 127 for character in filename)
        ):
            raise UploadError("invalid_filename")
        extension = PurePath(filename).suffix.lower()
        mime_by_extension = {
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".pdf": "application/pdf",
        }
        mime_type = mime_by_extension.get(extension)
        if mime_type is None:
            raise UploadError("unsupported_extension")
        accepted = {mime_type, "application/octet-stream"}
        if extension == ".md":
            accepted.add("text/plain")
        declared_type = content_type.split(";", 1)[0].strip().lower() if content_type else None
        if declared_type is not None and declared_type not in accepted:
            raise UploadError("mime_mismatch")
        if not data:
            raise UploadError("empty_file")
        if len(data) > self.max_bytes:
            raise UploadError("file_too_large")
        if extension == ".pdf" and not data.startswith(b"%PDF-"):
            raise UploadError("invalid_pdf_signature")
        if extension != ".pdf" and b"\x00" in data:
            raise UploadError("binary_text_file")
        return mime_type

    async def list_documents(self, owner_id: str) -> tuple[Document, ...]:
        return await self.repository.list_owned(owner_id)

    async def get_document(self, document_id: str, owner_id: str) -> Document | None:
        return await self.repository.get_document(document_id, owner_id)

    async def list_versions(self, document_id: str, owner_id: str) -> tuple[DocumentVersion, ...]:
        return await self.repository.list_versions(document_id, owner_id)

    async def get_version(
        self, version_id: str, owner_id: str
    ) -> tuple[DocumentVersion, tuple[DocumentSegment, ...], IngestionJob | None] | None:
        return await self.repository.get_version(version_id, owner_id)

    async def get_job(self, job_id: str, owner_id: str) -> IngestionJob | None:
        return await self.repository.get_job(job_id, owner_id)

    async def retry(self, job_id: str, owner_id: str, trace_id: str) -> IngestionJob | None:
        return await self.repository.retry(job_id, owner_id, trace_id)

    async def reprocess(self, version_id: str, owner_id: str, trace_id: str) -> IngestionJob | None:
        return await self.repository.reprocess(version_id, owner_id, trace_id)

    async def cancel(self, job_id: str, owner_id: str) -> IngestionJob | None:
        return await self.repository.cancel(job_id, owner_id)

    async def run_once(self) -> bool:
        claim = await self.repository.claim_next(self.timeout_seconds * 2 + 10)
        if claim is None:
            return False
        job, version = claim
        try:
            data = await asyncio.to_thread(self.store.get, version.object_key)
            extraction = await asyncio.wait_for(
                asyncio.to_thread(extract, data, version.mime_type), self.timeout_seconds
            )
        except asyncio.CancelledError:
            raise
        except TimeoutError:
            await self.repository.fail(job.id, job.attempts, "parser_timeout")
        except ParseError as error:
            await self.repository.fail(job.id, job.attempts, error.code)
        except (OSError, ValueError):
            await self.repository.fail(job.id, job.attempts, "object_unavailable")
        except Exception:
            logger.exception("ingestion parser failed", extra={"job_id": job.id})
            await self.repository.fail(job.id, job.attempts, "parser_error")
        else:
            await self.repository.complete(job.id, job.attempts, extraction)
        return True

    async def _run(self) -> None:
        while True:
            try:
                processed = await self.run_once()
                if not processed:
                    await asyncio.sleep(0.25)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("ingestion worker iteration failed")
                await asyncio.sleep(1)
