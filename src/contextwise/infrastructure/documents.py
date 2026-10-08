"""Owner-scoped document persistence and a leased PostgreSQL work queue."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from contextwise.application.ingestion.parsers import Extraction
from contextwise.infrastructure.models import (
    Document,
    DocumentSegment,
    DocumentVersion,
    IngestionJob,
)


class DocumentRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def add_upload(
        self,
        owner_id: str,
        filename: str,
        mime_type: str,
        data_size: int,
        digest: str,
        trace_id: str,
    ) -> tuple[Document, DocumentVersion, IngestionJob, bool]:
        now = datetime.now(UTC)
        async with self.session_factory.begin() as session:
            await session.execute(
                insert(Document)
                .values(id=str(uuid4()), owner_id=owner_id, filename=filename, created_at=now)
                .on_conflict_do_nothing(constraint="uq_document_owner_filename")
            )
            document = await session.scalar(
                select(Document)
                .where(Document.owner_id == owner_id, Document.filename == filename)
                .with_for_update()
            )
            assert document is not None
            version = await session.scalar(
                select(DocumentVersion).where(
                    DocumentVersion.document_id == document.id, DocumentVersion.sha256 == digest
                )
            )
            duplicate = version is not None
            if version is None:
                number = await session.scalar(
                    select(func.coalesce(func.max(DocumentVersion.number), 0)).where(
                        DocumentVersion.document_id == document.id
                    )
                )
                version = DocumentVersion(
                    id=str(uuid4()),
                    document_id=document.id,
                    number=int(number or 0) + 1,
                    sha256=digest,
                    mime_type=mime_type,
                    size_bytes=data_size,
                    object_key=digest,
                    extracted_text=None,
                    status="pending",
                    error_code=None,
                    created_at=now,
                    updated_at=now,
                )
                session.add(version)
                await session.flush()
                job = self._new_job(version.id, trace_id, now)
                session.add(job)
            else:
                existing_job = await session.scalar(
                    select(IngestionJob)
                    .where(IngestionJob.version_id == version.id)
                    .order_by(IngestionJob.created_at.desc())
                    .limit(1)
                )
                assert existing_job is not None
                job = existing_job
            return document, version, job, duplicate

    async def list_owned(self, owner_id: str) -> tuple[Document, ...]:
        async with self.session_factory() as session:
            result = await session.scalars(
                select(Document)
                .where(Document.owner_id == owner_id)
                .order_by(Document.created_at.desc())
            )
            return tuple(result)

    async def get_document(self, document_id: str, owner_id: str) -> Document | None:
        async with self.session_factory() as session:
            document: Document | None = await session.scalar(
                select(Document).where(Document.id == document_id, Document.owner_id == owner_id)
            )
            return document

    async def list_versions(self, document_id: str, owner_id: str) -> tuple[DocumentVersion, ...]:
        async with self.session_factory() as session:
            result = await session.scalars(
                select(DocumentVersion)
                .join(Document)
                .where(Document.id == document_id, Document.owner_id == owner_id)
                .order_by(DocumentVersion.number.desc())
            )
            return tuple(result)

    async def get_version(
        self, version_id: str, owner_id: str
    ) -> tuple[DocumentVersion, tuple[DocumentSegment, ...], IngestionJob | None] | None:
        async with self.session_factory() as session:
            version = await session.scalar(
                select(DocumentVersion)
                .join(Document)
                .where(DocumentVersion.id == version_id, Document.owner_id == owner_id)
            )
            if version is None:
                return None
            segments = await session.scalars(
                select(DocumentSegment)
                .where(DocumentSegment.version_id == version_id)
                .order_by(DocumentSegment.ordinal)
            )
            job = await session.scalar(
                select(IngestionJob)
                .where(IngestionJob.version_id == version_id)
                .order_by(IngestionJob.created_at.desc())
                .limit(1)
            )
            return version, tuple(segments), job

    async def get_job(self, job_id: str, owner_id: str) -> IngestionJob | None:
        async with self.session_factory() as session:
            job: IngestionJob | None = await session.scalar(
                select(IngestionJob)
                .join(DocumentVersion)
                .join(Document)
                .where(IngestionJob.id == job_id, Document.owner_id == owner_id)
            )
            return job

    async def claim_next(self, lease_seconds: float) -> tuple[IngestionJob, DocumentVersion] | None:
        now = datetime.now(UTC)
        async with self.session_factory.begin() as session:
            job = await session.scalar(
                select(IngestionJob)
                .where(
                    (IngestionJob.status == "pending")
                    | ((IngestionJob.status == "processing") & (IngestionJob.lease_until < now))
                )
                .order_by(IngestionJob.created_at)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if job is None:
                return None
            version = await session.get(DocumentVersion, job.version_id)
            assert version is not None
            job.status = "processing"
            job.attempts += 1
            job.lease_until = now + timedelta(seconds=lease_seconds)
            job.updated_at = now
            version.status = "processing"
            version.updated_at = now
            return job, version

    async def complete(self, job_id: str, attempt: int, extraction: Extraction) -> bool:
        now = datetime.now(UTC)
        async with self.session_factory.begin() as session:
            job = await session.get(IngestionJob, job_id, with_for_update=True)
            if job is None or job.status != "processing" or job.attempts != attempt:
                return False
            version = await session.get(DocumentVersion, job.version_id)
            assert version is not None
            await session.execute(
                delete(DocumentSegment).where(DocumentSegment.version_id == version.id)
            )
            session.add_all(
                DocumentSegment(
                    id=str(uuid4()),
                    version_id=version.id,
                    ordinal=index,
                    text=segment.text,
                    page=segment.page,
                    section=segment.section,
                    start_offset=segment.start_offset,
                    end_offset=segment.end_offset,
                )
                for index, segment in enumerate(extraction.segments)
            )
            version.extracted_text = extraction.text
            version.status = "completed"
            version.error_code = None
            version.updated_at = now
            job.status = "completed"
            job.error_code = None
            job.lease_until = None
            job.updated_at = now
            return True

    async def fail(self, job_id: str, attempt: int, code: str) -> bool:
        now = datetime.now(UTC)
        async with self.session_factory.begin() as session:
            job = await session.get(IngestionJob, job_id, with_for_update=True)
            if job is None or job.status != "processing" or job.attempts != attempt:
                return False
            version = await session.get(DocumentVersion, job.version_id)
            assert version is not None
            job.status = "failed"
            job.error_code = code
            job.lease_until = None
            job.updated_at = now
            version.status = "failed"
            version.error_code = code
            version.updated_at = now
            return True

    async def retry(self, job_id: str, owner_id: str, trace_id: str) -> IngestionJob | None:
        now = datetime.now(UTC)
        async with self.session_factory.begin() as session:
            job = await session.scalar(
                select(IngestionJob)
                .join(DocumentVersion)
                .join(Document)
                .where(IngestionJob.id == job_id, Document.owner_id == owner_id)
                .with_for_update()
            )
            if job is None or job.status not in {"failed", "cancelled"}:
                return None
            version = await session.get(DocumentVersion, job.version_id, with_for_update=True)
            assert version is not None
            latest_job = await session.scalar(
                select(IngestionJob)
                .where(IngestionJob.version_id == version.id)
                .order_by(IngestionJob.created_at.desc())
                .limit(1)
            )
            if latest_job is None or latest_job.id != job.id:
                return None
            job.status = "pending"
            job.error_code = None
            job.trace_id = trace_id
            job.updated_at = now
            version.status = "pending"
            version.error_code = None
            version.updated_at = now
            return job

    async def reprocess(self, version_id: str, owner_id: str, trace_id: str) -> IngestionJob | None:
        now = datetime.now(UTC)
        async with self.session_factory.begin() as session:
            version = await session.scalar(
                select(DocumentVersion)
                .join(Document)
                .where(DocumentVersion.id == version_id, Document.owner_id == owner_id)
                .with_for_update()
            )
            if version is None or version.status in {"pending", "processing"}:
                return None
            await session.execute(
                delete(DocumentSegment).where(DocumentSegment.version_id == version.id)
            )
            version.extracted_text = None
            version.status = "pending"
            version.error_code = None
            version.updated_at = now
            job = self._new_job(version.id, trace_id, now)
            session.add(job)
            return job

    async def cancel(self, job_id: str, owner_id: str) -> IngestionJob | None:
        now = datetime.now(UTC)
        async with self.session_factory.begin() as session:
            job = await session.scalar(
                select(IngestionJob)
                .join(DocumentVersion)
                .join(Document)
                .where(IngestionJob.id == job_id, Document.owner_id == owner_id)
                .with_for_update()
            )
            if job is None or job.status not in {"pending", "processing"}:
                return None
            version = await session.get(DocumentVersion, job.version_id)
            assert version is not None
            job.status = "cancelled"
            job.lease_until = None
            job.updated_at = now
            version.status = "cancelled"
            version.updated_at = now
            return job

    @staticmethod
    def _new_job(version_id: str, trace_id: str, now: datetime) -> IngestionJob:
        return IngestionJob(
            id=str(uuid4()),
            version_id=version_id,
            status="pending",
            attempts=0,
            error_code=None,
            trace_id=trace_id,
            lease_until=None,
            created_at=now,
            updated_at=now,
        )
