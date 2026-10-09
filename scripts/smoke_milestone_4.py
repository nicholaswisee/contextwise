"""Live HTTP smoke demo for the Milestone 4 cited retrieval slice."""

import asyncio
import json
import os
from pathlib import Path
from uuid import uuid4

import httpx


async def main() -> None:
    owner_token = os.environ["CONTEXTWISE_OWNER_TOKEN"]
    base_url = os.environ.get("CONTEXTWISE_BASE_URL", "http://127.0.0.1:8000")
    headers = {"X-Contextwise-Owner": owner_token}
    async with httpx.AsyncClient(base_url=base_url, timeout=30, trust_env=False) as client:
        for _ in range(30):
            try:
                ready = await client.get("/health/ready")
                if ready.status_code == 200:
                    break
            except httpx.TransportError:
                pass
            await asyncio.sleep(1)
        else:
            raise RuntimeError("API did not become ready")

        key = str(uuid4())[:8]
        upload = await client.post(
            "/v1/documents",
            headers=headers,
            files={
                "file": (
                    f"rag-demo-{key}.md",
                    b"# Station guide\n\nThe station signal is amber fox. "
                    b"The station exit is east hatch.",
                    "text/markdown",
                )
            },
        )
        upload.raise_for_status()
        version_id = upload.json()["version"]["id"]
        for _ in range(30):
            version = await client.get(f"/v1/document-versions/{version_id}", headers=headers)
            version.raise_for_status()
            if version.json()["status"] == "completed":
                break
            if version.json()["status"] == "failed":
                raise RuntimeError(f"ingestion failed: {version.json()['error_code']}")
            await asyncio.sleep(1)
        else:
            raise RuntimeError("ingestion did not finish")

        collection = await client.post(
            "/v1/rag/collections", headers=headers, json={"name": f"demo-{key}"}
        )
        collection.raise_for_status()
        collection_id = collection.json()["id"]
        added = await client.put(
            f"/v1/rag/collections/{collection_id}/documents/{upload.json()['document']['id']}",
            headers=headers,
        )
        added.raise_for_status()
        index = await client.post(
            f"/v1/rag/collections/{collection_id}/indexes",
            headers=headers,
            json={"chunk": {"size": 40, "overlap": 4, "strategy": "heading"}},
        )
        index.raise_for_status()
        assert index.json()["chunk_count"] == 1

        answer = await client.post(
            f"/v1/rag/collections/{collection_id}/ask",
            headers=headers,
            json={"query": "What is the station signal?", "config": {"min_score": 0.0}},
        )
        answer.raise_for_status()
        assert answer.json()["status"] == "answered"
        assert "amber fox" in answer.json()["answer"]
        assert "[E1]" in answer.json()["answer"]
        evidence_id = answer.json()["selected"][0]["id"]
        passage = await client.get(f"/v1/rag/evidence/{evidence_id}", headers=headers)
        passage.raise_for_status()
        assert "amber fox" in passage.json()["text"]
        trace = await client.get(f"/v1/rag/runs/{answer.json()['run_id']}", headers=headers)
        trace.raise_for_status()
        assert evidence_id in trace.json()["selected_evidence_ids"]

        unsupported = await client.post(
            f"/v1/rag/collections/{collection_id}/ask",
            headers=headers,
            json={"query": "What is the lunar timetable?", "config": {"min_score": 0.99}},
        )
        unsupported.raise_for_status()
        assert unsupported.json()["status"] == "insufficient_evidence"
        assert unsupported.json()["answer"].startswith("I cannot")
        inspect = await client.post(
            f"/v1/rag/collections/{collection_id}/retrieve",
            headers=headers,
            json={"query": "station signal amber fox", "config": {"top_k": 1, "min_score": 0.0}},
        )
        inspect.raise_for_status()
        assert inspect.json()["status"] == "retrieval_only"
        assert len(inspect.json()["candidates"]) == 1
        trace_path = os.environ.get("CONTEXTWISE_RAG_TRACE_PATH")
        if trace_path:
            Path(trace_path).write_text(
                json.dumps(
                    {
                        "success": {
                            "answer": answer.json(),
                            "passage": passage.json(),
                            "run": trace.json(),
                        },
                        "failure": unsupported.json(),
                        "retrieval_only": inspect.json(),
                    },
                    indent=2,
                )
                + "\n"
            )
        print("PASS M4: cited answer, open citation, abstention, retrieval trace")
        print(
            f"collection={collection_id} index={index.json()['id']} run={answer.json()['run_id']}"
        )


if __name__ == "__main__":
    asyncio.run(main())
