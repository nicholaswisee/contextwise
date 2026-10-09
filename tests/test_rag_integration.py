from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from contextwise.api.dependencies import get_state
from contextwise.api.main import create_app
from contextwise.application.rag.embeddings import HashEmbeddingClient
from contextwise.config import Settings

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_rag_collection_reindex_citations_and_trace(monkeypatch, apply_migrations) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://contextwise:contextwise@localhost:5434/contextwise_test",
    )
    app = create_app(Settings())
    headers = {"X-Contextwise-Owner": "local-development-token"}
    filename = f"rag-{uuid4()}.md"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        unauthorized = await client.post("/v1/rag/collections", json={"name": "private"})
        assert unauthorized.status_code == 401
        empty = await client.post(
            "/v1/rag/collections", headers=headers, json={"name": str(uuid4())}
        )
        collection_id = empty.json()["id"]
        no_index = await client.post(
            f"/v1/rag/collections/{collection_id}/ask",
            headers=headers,
            json={"query": "What is the launch code?"},
        )
        assert no_index.json()["status"] == "insufficient_evidence"
        assert no_index.json()["candidates"] == []

        upload = await client.post(
            "/v1/documents",
            headers=headers,
            files={
                "file": (filename, b"# Launch\n\nThe launch code is amber fox.", "text/markdown")
            },
        )
        assert upload.status_code == 202
        assert await get_state().ingestion_service.run_once()
        document_id = upload.json()["document"]["id"]
        added = await client.put(
            f"/v1/rag/collections/{collection_id}/documents/{document_id}", headers=headers
        )
        assert added.status_code == 204
        index = await client.post(
            f"/v1/rag/collections/{collection_id}/indexes",
            headers=headers,
            json={"chunk": {"size": 8, "overlap": 2, "strategy": "heading"}},
        )
        assert index.status_code == 201, index.text
        assert index.json()["chunk_count"] == 1

        answer = await client.post(
            f"/v1/rag/collections/{collection_id}/ask",
            headers=headers,
            json={"query": "launch code amber fox", "config": {"min_score": 0.0}},
        )
        assert answer.status_code == 200, answer.text
        body = answer.json()
        assert body["status"] == "answered"
        assert "[E1]" in body["answer"]
        assert body["index_id"] == index.json()["id"]
        evidence_id = body["selected"][0]["id"]
        citation = await client.get(f"/v1/rag/evidence/{evidence_id}", headers=headers)
        assert citation.status_code == 200
        assert citation.json()["filename"] == filename
        assert citation.json()["text"] in body["answer"]
        version_detail = await client.get(
            f"/v1/document-versions/{upload.json()['version']['id']}", headers=headers
        )
        source_segment = version_detail.json()["segments"][0]
        assert citation.json()["source_start_offset"] == source_segment["start_offset"]
        assert citation.json()["source_end_offset"] == source_segment["end_offset"]
        assert (
            source_segment["text"][
                citation.json()["segment_start_offset"] : citation.json()["segment_end_offset"]
            ]
            == citation.json()["text"]
        )
        trace = await client.get(f"/v1/rag/runs/{body['run_id']}", headers=headers)
        assert trace.json()["candidates"][0]["id"] == evidence_id
        assert trace.json()["selected_evidence_ids"] == [evidence_id]
        invalid_generated = await client.post(
            f"/v1/rag/collections/{collection_id}/ask",
            headers=headers,
            json={
                "query": "launch code amber fox",
                "generation_model": "fake-default",
                "config": {"min_score": 0.0},
            },
        )
        assert invalid_generated.json()["status"] == "invalid_citation"
        assert invalid_generated.json()["answer"].startswith("I cannot")
        fake = get_state().llm_clients["fake-default"]
        monkeypatch.setattr(fake, "text", "The code is amber fox [E1]")
        qualified = await client.post(
            f"/v1/rag/collections/{collection_id}/ask",
            headers=headers,
            json={
                "query": "launch code amber fox",
                "generation_model": "fake-default",
                "config": {"min_score": 0.0},
            },
        )
        assert qualified.json()["status"] == "qualified_answer"
        assert qualified.json()["answer"].startswith("Unverified generated answer:")

        class FailingEmbedding(HashEmbeddingClient):
            async def embed(self, texts):
                return []

        service = get_state().rag_service
        original_embedding = service.embedding
        service.embedding = FailingEmbedding("v1")
        failed_index = await client.post(
            f"/v1/rag/collections/{collection_id}/indexes",
            headers=headers,
            json={"chunk": {"size": 8, "overlap": 2}},
        )
        assert failed_index.status_code == 502
        collection_after_failure = await client.get("/v1/rag/collections", headers=headers)
        active = next(row for row in collection_after_failure.json() if row["id"] == collection_id)
        assert active["active_index_id"] == index.json()["id"]
        service.embedding = original_embedding

        retrieval = await client.post(
            f"/v1/rag/collections/{collection_id}/retrieve",
            headers=headers,
            json={"query": "launch code amber fox", "config": {"min_score": 0.0}},
        )
        assert retrieval.json()["status"] == "retrieval_only"
        unsupported = await client.post(
            f"/v1/rag/collections/{collection_id}/ask",
            headers=headers,
            json={"query": "unrelated astronomy", "config": {"min_score": 0.99}},
        )
        assert unsupported.json()["status"] == "insufficient_evidence"
        assert unsupported.json()["answer"].startswith("I cannot")

        other_collection = await client.post(
            "/v1/rag/collections", headers=headers, json={"name": str(uuid4())}
        )
        other = await client.post(
            f"/v1/rag/collections/{other_collection.json()['id']}/retrieve",
            headers=headers,
            json={"query": "launch code", "config": {"min_score": -1.0}},
        )
        assert other.json()["candidates"] == []
        assert not await get_state().rag_repository.add_document(
            "another-owner", collection_id, document_id
        )
        assert await get_state().rag_repository.get_evidence("another-owner", evidence_id) is None

        revised = await client.post(
            "/v1/documents",
            headers=headers,
            files={
                "file": (filename, b"# Launch\n\nThe launch code is violet bird.", "text/markdown")
            },
        )
        assert revised.status_code == 202
        assert await get_state().ingestion_service.run_once()
        next_index = await client.post(
            f"/v1/rag/collections/{collection_id}/indexes",
            headers=headers,
            json={"chunk": {"size": 8, "overlap": 2, "strategy": "heading"}},
        )
        assert next_index.json()["number"] == index.json()["number"] + 1
        after = await client.post(
            f"/v1/rag/collections/{collection_id}/retrieve",
            headers=headers,
            json={"query": "launch code violet bird", "config": {"min_score": -1.0}},
        )
        assert after.json()["index_id"] == next_index.json()["id"]
        assert all("amber fox" not in row["text"] for row in after.json()["candidates"])
        old_citation = await client.get(f"/v1/rag/evidence/{evidence_id}", headers=headers)
        assert old_citation.status_code == 200
