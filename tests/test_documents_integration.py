import asyncio
import io
import time
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from reportlab.pdfgen import canvas

from contextwise.api.dependencies import get_state
from contextwise.api.main import create_app
from contextwise.application.ingestion import service as ingestion_module
from contextwise.config import Settings
from contextwise.infrastructure.models import IngestionJob

pytestmark = pytest.mark.integration


def _pdf(text: str) -> bytes:
    stream = io.BytesIO()
    page = canvas.Canvas(stream)
    page.drawString(72, 720, text)
    page.save()
    return stream.getvalue()


@pytest.fixture
def app_with_db(monkeypatch, apply_migrations, tmp_path):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://contextwise:contextwise@localhost:5434/contextwise_test",
    )
    monkeypatch.setenv("CONTEXTWISE_DOCUMENT_STORE_PATH", str(tmp_path))
    return create_app(Settings())


@pytest.mark.asyncio
async def test_upload_dedup_version_provenance_and_owner_boundary(app_with_db) -> None:
    headers = {"X-Contextwise-Owner": "local-development-token"}
    async with AsyncClient(
        transport=ASGITransport(app=app_with_db), base_url="http://test"
    ) as client:
        denied = await client.post(
            "/v1/documents", files={"file": ("note.txt", b"A", "text/plain")}
        )
        assert denied.status_code == 401
        first = await client.post(
            "/v1/documents",
            headers=headers,
            files={"file": ("note.txt", b"First passage.\n\nSecond passage.", "text/plain")},
        )
        assert first.status_code == 202
        assert await get_state().ingestion_service.run_once()
        first_detail = await client.get(
            f"/v1/document-versions/{first.json()['version']['id']}", headers=headers
        )
        assert first_detail.json()["status"] == "completed"
        assert [row["text"] for row in first_detail.json()["segments"]] == [
            "First passage.",
            "Second passage.",
        ]
        assert all(row["page"] is None for row in first_detail.json()["segments"])
        assert first_detail.json()["extracted_text"] == "First passage.\n\nSecond passage."

        duplicate = await client.post(
            "/v1/documents",
            headers=headers,
            files={"file": ("note.txt", b"First passage.\n\nSecond passage.", "text/plain")},
        )
        assert duplicate.json()["duplicate"] is True
        assert duplicate.json()["version"]["id"] == first.json()["version"]["id"]
        assert not await get_state().ingestion_service.run_once()

        revised = await client.post(
            "/v1/documents",
            headers=headers,
            files={"file": ("note.txt", b"Revised passage.", "text/plain")},
        )
        assert revised.json()["document"]["id"] == first.json()["document"]["id"]
        assert revised.json()["version"]["number"] == 2
        assert await get_state().ingestion_service.run_once()
        document = await client.get(
            f"/v1/documents/{first.json()['document']['id']}", headers=headers
        )
        assert len(document.json()["versions"]) == 2
        hidden = await client.get(
            f"/v1/document-versions/{first.json()['version']['id']}",
            headers={"X-Contextwise-Owner": "wrong"},
        )
        assert hidden.status_code == 401


@pytest.mark.asyncio
async def test_pdf_failure_retry_reprocess_and_rejected_upload(app_with_db) -> None:
    headers = {"X-Contextwise-Owner": "local-development-token"}
    async with AsyncClient(
        transport=ASGITransport(app=app_with_db), base_url="http://test"
    ) as client:
        unsupported = await client.post(
            "/v1/documents",
            headers=headers,
            files={"file": ("image.png", b"payload", "image/png")},
        )
        assert unsupported.status_code == 422
        corrupt = await client.post(
            "/v1/documents",
            headers=headers,
            files={"file": ("broken.pdf", b"%PDF-broken", "application/pdf")},
        )
        assert corrupt.status_code == 202
        assert await get_state().ingestion_service.run_once()
        failed = await client.get(
            f"/v1/ingestion-jobs/{corrupt.json()['job']['id']}", headers=headers
        )
        assert failed.json()["status"] == "failed"
        assert failed.json()["error_code"] == "invalid_pdf"
        retried = await client.post(
            f"/v1/ingestion-jobs/{corrupt.json()['job']['id']}/retry", headers=headers
        )
        assert retried.status_code == 202
        assert await get_state().ingestion_service.run_once()
        failed_again = await client.get(
            f"/v1/ingestion-jobs/{corrupt.json()['job']['id']}", headers=headers
        )
        assert failed_again.json()["attempts"] == 2

        valid = await client.post(
            "/v1/documents",
            headers=headers,
            files={"file": ("page.pdf", _pdf("Page source"), "application/pdf")},
        )
        assert await get_state().ingestion_service.run_once()
        detail = await client.get(
            f"/v1/document-versions/{valid.json()['version']['id']}", headers=headers
        )
        assert detail.json()["segments"][0]["page"] == 1
        assert detail.json()["segments"][0]["text"] == "Page source"
        reprocess = await client.post(
            f"/v1/document-versions/{valid.json()['version']['id']}/reprocess", headers=headers
        )
        assert reprocess.status_code == 202
        assert await get_state().ingestion_service.run_once()
        detail_after = await client.get(
            f"/v1/document-versions/{valid.json()['version']['id']}", headers=headers
        )
        assert len(detail_after.json()["segments"]) == 1

        new_job = await client.post(
            f"/v1/document-versions/{corrupt.json()['version']['id']}/reprocess",
            headers=headers,
        )
        assert new_job.status_code == 202
        stale_retry = await client.post(
            f"/v1/ingestion-jobs/{corrupt.json()['job']['id']}/retry", headers=headers
        )
        assert stale_retry.status_code == 409


@pytest.mark.asyncio
async def test_worker_reclaims_expired_lease_without_duplicate_segments(app_with_db) -> None:
    headers = {"X-Contextwise-Owner": "local-development-token"}
    while await get_state().ingestion_service.run_once():
        pass
    async with AsyncClient(
        transport=ASGITransport(app=app_with_db), base_url="http://test"
    ) as client:
        response = await client.post(
            "/v1/documents",
            headers=headers,
            files={"file": ("restart.txt", b"One passage", "text/plain")},
        )
        job_id = response.json()["job"]["id"]
        repository = get_state().document_repository
        claim = await repository.claim_next(30)
        assert claim is not None
        assert await repository.claim_next(30) is None
        async with repository.session_factory.begin() as session:
            job = await session.get(IngestionJob, job_id)
            assert job is not None
            job.lease_until = datetime.now(UTC) - timedelta(seconds=1)
        assert await get_state().ingestion_service.run_once()
        assert not await repository.fail(job_id, claim[0].attempts, "late_worker_failure")
        detail = await client.get(
            f"/v1/document-versions/{response.json()['version']['id']}", headers=headers
        )
        assert detail.json()["status"] == "completed"
        assert len(detail.json()["segments"]) == 1
        assert detail.json()["job"]["attempts"] == 2


@pytest.mark.asyncio
async def test_timeout_cancel_retry_and_size_limit(app_with_db, monkeypatch) -> None:
    headers = {"X-Contextwise-Owner": "local-development-token"}
    service = get_state().ingestion_service
    original_extract = ingestion_module.extract

    def slow_extract(data: bytes, mime_type: str):
        time.sleep(0.05)
        return original_extract(data, mime_type)

    async with AsyncClient(
        transport=ASGITransport(app=app_with_db), base_url="http://test"
    ) as client:
        service.max_bytes = 4
        oversized = await client.post(
            "/v1/documents",
            headers=headers,
            files={"file": ("large.txt", b"12345", "text/plain")},
        )
        assert oversized.status_code == 422
        service.max_bytes = 100
        response = await client.post(
            "/v1/documents",
            headers=headers,
            files={"file": ("timeout.txt", b"Text", "text/plain")},
        )
        monkeypatch.setattr("contextwise.application.ingestion.service.extract", slow_extract)
        service.timeout_seconds = 0.001
        assert await service.run_once()
        failed = await client.get(
            f"/v1/ingestion-jobs/{response.json()['job']['id']}", headers=headers
        )
        assert failed.json()["error_code"] == "parser_timeout"
        monkeypatch.setattr("contextwise.application.ingestion.service.extract", original_extract)
        service.timeout_seconds = 30
        retry = await client.post(
            f"/v1/ingestion-jobs/{response.json()['job']['id']}/retry", headers=headers
        )
        assert retry.status_code == 202
        assert await service.run_once()
        completed = await client.get(
            f"/v1/document-versions/{response.json()['version']['id']}", headers=headers
        )
        assert completed.json()["status"] == "completed"

        pending = await client.post(
            "/v1/documents",
            headers=headers,
            files={"file": ("cancel.txt", b"Text", "text/plain")},
        )
        cancelled = await client.post(
            f"/v1/ingestion-jobs/{pending.json()['job']['id']}/cancel", headers=headers
        )
        assert cancelled.json()["status"] == "cancelled"
        assert not await service.run_once()


@pytest.mark.asyncio
async def test_concurrent_duplicate_upload_claims_one_version(app_with_db) -> None:
    service = get_state().ingestion_service
    first, second = await asyncio.gather(
        service.upload("local", "parallel.txt", "text/plain", b"Same bytes", "trace-one"),
        service.upload("local", "parallel.txt", "text/plain", b"Same bytes", "trace-two"),
    )
    assert first.document.id == second.document.id
    assert first.version.id == second.version.id
    assert first.job.id == second.job.id
    assert {first.duplicate, second.duplicate} == {False, True}
    assert await service.run_once()
    assert not await service.run_once()
