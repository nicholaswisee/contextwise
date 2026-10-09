"""Run the frozen 50-question RAG baseline through the public API and PostgreSQL."""

import asyncio
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from contextwise.api.dependencies import get_state
from contextwise.api.main import create_app
from contextwise.config import Settings

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "datasets/retrieval/v1/cases.json"
OUTPUT = ROOT / "docs/evaluations/04-rag-baseline.json"
EXPERIMENTS = [
    {
        "name": "baseline",
        "size": 24,
        "overlap": 4,
        "strategy": "fixed",
        "top_k": 5,
        "rewrite": False,
        "model": "hash-256-v1",
    },
    {
        "name": "short_chunks",
        "size": 16,
        "overlap": 4,
        "strategy": "fixed",
        "top_k": 5,
        "rewrite": False,
        "model": "hash-256-v1",
    },
    {
        "name": "long_chunks",
        "size": 40,
        "overlap": 4,
        "strategy": "fixed",
        "top_k": 5,
        "rewrite": False,
        "model": "hash-256-v1",
    },
    {
        "name": "no_overlap",
        "size": 24,
        "overlap": 0,
        "strategy": "fixed",
        "top_k": 5,
        "rewrite": False,
        "model": "hash-256-v1",
    },
    {
        "name": "top_one",
        "size": 24,
        "overlap": 4,
        "strategy": "fixed",
        "top_k": 1,
        "rewrite": False,
        "model": "hash-256-v1",
    },
    {
        "name": "heading_aware",
        "size": 24,
        "overlap": 4,
        "strategy": "heading",
        "top_k": 5,
        "rewrite": False,
        "model": "hash-256-v1",
    },
    {
        "name": "query_rewrite",
        "size": 24,
        "overlap": 4,
        "strategy": "fixed",
        "top_k": 5,
        "rewrite": True,
        "model": "hash-256-v1",
    },
    {
        "name": "embedding_v2",
        "size": 24,
        "overlap": 4,
        "strategy": "fixed",
        "top_k": 5,
        "rewrite": False,
        "model": "hash-256-v2",
    },
]


async def main() -> None:
    dataset = json.loads(DATASET.read_text())
    assert sum(len(document["facts"]) for document in dataset["documents"]) == 50
    settings = Settings()
    app = create_app(settings)
    headers = {"X-Contextwise-Owner": settings.owner_token}
    run_key = str(uuid4())[:8]
    results: list[dict[str, object]] = []
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://eval", timeout=120
    ) as client:
        collection = await client.post(
            "/v1/rag/collections", headers=headers, json={"name": f"eval-{run_key}"}
        )
        collection.raise_for_status()
        collection_id = collection.json()["id"]
        document_ids: dict[str, str] = {}
        for document in dataset["documents"]:
            text = f"# {document['heading']}\n\n" + " ".join(
                fact["statement"] for fact in document["facts"]
            )
            response = await client.post(
                "/v1/documents",
                headers=headers,
                files={
                    "file": (f"eval-{run_key}-{document['name']}", text.encode(), "text/markdown")
                },
            )
            response.raise_for_status()
            assert await get_state().ingestion_service.run_once()
            document_id = response.json()["document"]["id"]
            document_ids[document["name"]] = document_id
            added = await client.put(
                f"/v1/rag/collections/{collection_id}/documents/{document_id}", headers=headers
            )
            added.raise_for_status()
        for experiment in EXPERIMENTS:
            index = await client.post(
                f"/v1/rag/collections/{collection_id}/indexes",
                headers=headers,
                json={
                    "chunk": {
                        "size": experiment["size"],
                        "overlap": experiment["overlap"],
                        "strategy": experiment["strategy"],
                    },
                    "embedding_model": experiment["model"],
                },
            )
            index.raise_for_status()
            cases: list[dict[str, object]] = []
            for document in dataset["documents"]:
                for fact in document["facts"]:
                    response = await client.post(
                        f"/v1/rag/collections/{collection_id}/ask",
                        headers=headers,
                        json={
                            "query": fact["question"],
                            "generation_model": "extractive",
                            "config": {
                                "top_k": experiment["top_k"],
                                "min_score": 0.1,
                                "context_tokens": 200,
                                "query_rewrite": experiment["rewrite"],
                            },
                        },
                    )
                    response.raise_for_status()
                    output = response.json()
                    relevant = [
                        item
                        for item in output["candidates"]
                        if item["document_id"] == document_ids[document["name"]]
                        and fact["answer"].casefold() in item["text"].casefold()
                    ]
                    selected = output["selected"]
                    answer = output["answer"] or ""
                    quote = re.search(r'The source says: "(.*)" \[E\d+\]$', answer)
                    reference = re.search(r"\[(E\d+)\]$", answer)
                    cited = (
                        next(
                            (
                                item
                                for item in selected
                                if item["citation_id"] == reference.group(1)
                            ),
                            None,
                        )
                        if reference
                        else None
                    )
                    resolved = None
                    if cited is not None:
                        citation_response = await client.get(
                            f"/v1/rag/evidence/{cited['id']}", headers=headers
                        )
                        if citation_response.status_code == 200:
                            resolved = citation_response.json()
                    cases.append(
                        {
                            "question": fact["question"],
                            "expected_document": document["name"],
                            "expected_answer": fact["answer"],
                            "run_id": output["run_id"],
                            "recall": bool(relevant),
                            "answer_support": fact["answer"].casefold() in answer.casefold()
                            and quote is not None
                            and any(quote.group(1) in item["text"] for item in selected),
                            "citation_valid": output["status"] != "answered"
                            or (
                                quote is not None
                                and resolved is not None
                                and quote.group(1) in resolved["text"]
                            ),
                            "latency_ms": output["latency_ms"],
                            "status": output["status"],
                        }
                    )
            results.append(
                {
                    "experiment": experiment,
                    "index_id": index.json()["id"],
                    "chunk_count": index.json()["chunk_count"],
                    "recall_at_k": sum(bool(case["recall"]) for case in cases) / len(cases),
                    "answer_support_rate": sum(bool(case["answer_support"]) for case in cases)
                    / len(cases),
                    "citation_validity_rate": sum(bool(case["citation_valid"]) for case in cases)
                    / len(cases),
                    "mean_latency_ms": sum(int(case["latency_ms"]) for case in cases) / len(cases),
                    "estimated_cost_usd": 0,
                    "cases": cases,
                }
            )
    OUTPUT.write_text(
        json.dumps(
            {
                "dataset": str(DATASET.relative_to(ROOT)),
                "frozen_cases": 50,
                "generated_at": datetime.now(UTC).isoformat(),
                "collection_id": collection_id,
                "run_key": run_key,
                "results": results,
            },
            indent=2,
        )
        + "\n"
    )
    for result in results:
        print(
            result["experiment"]["name"],
            result["recall_at_k"],
            result["answer_support_rate"],
            result["mean_latency_ms"],
        )


if __name__ == "__main__":
    if not os.environ.get("DATABASE_URL"):
        raise SystemExit("Set DATABASE_URL to a migrated pgvector PostgreSQL database")
    asyncio.run(main())
