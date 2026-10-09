"""Exercise the running Docker API for the assistant and ingestion demos."""

import io
import json
import os
import time
from pathlib import Path
from uuid import uuid4

import httpx
from reportlab.pdfgen import canvas


def events(response: httpx.Response) -> list[dict[str, object]]:
    response.raise_for_status()
    return [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]


def terminal(response: httpx.Response) -> dict[str, object]:
    return next(event for event in events(response) if event["type"] == "completed")


def pdf_bytes(text: str) -> bytes:
    stream = io.BytesIO()
    page = canvas.Canvas(stream)
    page.drawString(72, 720, text)
    page.save()
    return stream.getvalue()


def wait_for_job(client: httpx.Client, job_id: str) -> dict[str, object]:
    for _ in range(100):
        response = client.get(f"/v1/ingestion-jobs/{job_id}")
        response.raise_for_status()
        job = response.json()
        if job["status"] in {"completed", "failed", "cancelled"}:
            return job
        time.sleep(0.1)
    raise RuntimeError("job did not reach a terminal state")


def main() -> None:
    owner_token = os.environ["CONTEXTWISE_OWNER_TOKEN"]
    base_url = os.environ.get("CONTEXTWISE_DEMO_BASE_URL", "http://127.0.0.1:8000")
    for _ in range(100):
        try:
            if httpx.get(f"{base_url}/health/ready", timeout=2).status_code == 200:
                break
        except httpx.TransportError:
            pass
        time.sleep(0.1)
    else:
        raise RuntimeError("API did not become ready")
    with httpx.Client(base_url=base_url, timeout=30) as anonymous:
        assert anonymous.post("/v1/generations", json={"prompt": "hello"}).status_code == 401
        assert anonymous.get("/v1/documents").status_code == 401

    with httpx.Client(
        base_url=base_url, headers={"X-Contextwise-Owner": owner_token}, timeout=30
    ) as client:
        created = client.post("/v1/conversations")
        created.raise_for_status()
        conversation_id = created.json()["id"]
        first = terminal(
            client.post(
                f"/v1/conversations/{conversation_id}/messages/stream",
                headers={"Idempotency-Key": f"demo-{uuid4()}"},
                json={"parts": [{"type": "text", "text": "My name is Ada."}]},
            )
        )
        second = terminal(
            client.post(
                f"/v1/conversations/{conversation_id}/messages/stream",
                headers={"Idempotency-Key": f"demo-{uuid4()}"},
                json={"parts": [{"type": "text", "text": "What name did I give?"}]},
            )
        )
        inspected = client.get(
            f"/v1/conversations/{conversation_id}/context/{second['message_id']}"
        )
        inspected.raise_for_status()
        provider_messages = inspected.json()["snapshot"]["provider_messages"]
        assert any("My name is Ada." in message["content"] for message in provider_messages)
        regenerated = terminal(
            client.post(
                f"/v1/messages/{second['message_id']}/regenerate/stream",
                headers={"Idempotency-Key": f"demo-{uuid4()}"},
            )
        )
        assert regenerated["message_id"] != second["message_id"]
        branched = client.post(f"/v1/messages/{first['message_id']}/branch")
        branched.raise_for_status()
        branch_id = branched.json()["id"]
        assert branch_id != conversation_id
        terminal(
            client.post(
                f"/v1/conversations/{branch_id}/messages/stream",
                headers={"Idempotency-Key": f"demo-{uuid4()}"},
                json={"parts": [{"type": "text", "text": "Continue this branch."}]},
            )
        )
        export_path = os.environ.get("CONTEXTWISE_DEMO_EXPORT_PATH")
        if export_path:
            conversation = client.get(f"/v1/conversations/{conversation_id}")
            conversation.raise_for_status()
            Path(export_path).write_text(
                json.dumps(
                    {
                        "conversation": conversation.json(),
                        "context": inspected.json(),
                        "branch_id": branch_id,
                    },
                    indent=2,
                )
                + "\n"
            )
        print("M2 live demo: owner gate, two turns, context, regenerate, branch PASS")

        suffix = uuid4().hex[:8]
        uploads = [
            (f"note-{suffix}.txt", b"First passage.\n\nSecond passage.", "text/plain"),
            (f"guide-{suffix}.md", b"# Guide\nA marked passage.", "text/markdown"),
            (f"page-{suffix}.pdf", pdf_bytes("Page provenance"), "application/pdf"),
        ]
        for filename, data, mime in uploads:
            response = client.post("/v1/documents", files={"file": (filename, data, mime)})
            response.raise_for_status()
            body = response.json()
            job = wait_for_job(client, body["job"]["id"])
            assert job["status"] == "completed"
            detail = client.get(f"/v1/document-versions/{body['version']['id']}")
            detail.raise_for_status()
            assert detail.json()["segments"]
            if mime == "application/pdf":
                assert detail.json()["segments"][0]["page"] == 1
            if mime == "text/markdown":
                assert detail.json()["segments"][0]["section"] == "Guide"
        duplicate = client.post("/v1/documents", files={"file": uploads[0]})
        duplicate.raise_for_status()
        assert duplicate.json()["duplicate"] is True
        corrupt = client.post(
            "/v1/documents",
            files={"file": (f"broken-{suffix}.pdf", b"%PDF-broken", "application/pdf")},
        )
        corrupt.raise_for_status()
        failed = wait_for_job(client, corrupt.json()["job"]["id"])
        assert failed["status"] == "failed" and failed["error_code"] == "invalid_pdf"
        retry = client.post(f"/v1/ingestion-jobs/{failed['id']}/retry")
        retry.raise_for_status()
        assert wait_for_job(client, failed["id"])["attempts"] == 2
        trace_path = os.environ.get("CONTEXTWISE_INGESTION_TRACE_PATH")
        if trace_path:
            Path(trace_path).write_text(
                json.dumps(
                    {
                        "successful_job": job,
                        "failed_job": failed,
                        "retried_job": client.get(f"/v1/ingestion-jobs/{failed['id']}").json(),
                    },
                    indent=2,
                )
                + "\n"
            )
        print("M3 live demo: TXT, Markdown, PDF, dedup, failure, retry PASS")


if __name__ == "__main__":
    main()
