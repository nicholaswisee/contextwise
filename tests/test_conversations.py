import json

import pytest
from httpx import ASGITransport, AsyncClient

from contextwise.api.main import create_app
from contextwise.config import Settings

pytestmark = pytest.mark.integration


@pytest.fixture
def app_with_db(monkeypatch, apply_migrations):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://contextwise:contextwise@localhost:5434/contextwise_test",
    )
    return create_app(Settings())


def owner_headers(key: str = "turn-1") -> dict[str, str]:
    return {"X-Contextwise-Owner": "local-development-token", "Idempotency-Key": key}


def completed_event(body: str) -> dict[str, object]:
    events = [
        json.loads(line.removeprefix("data: "))
        for line in body.splitlines()
        if line.startswith("data: ")
    ]
    return next(event for event in events if event["type"] == "completed")


@pytest.mark.asyncio
async def test_conversation_routes_require_owner_token(app_with_db) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app_with_db), base_url="http://test"
    ) as client:
        response = await client.post("/v1/conversations")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_stream_reusing_completed_key_replays_one_assistant_result(app_with_db) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app_with_db), base_url="http://test"
    ) as client:
        created = await client.post("/v1/conversations", headers=owner_headers())
        conversation_id = created.json()["id"]
        payload = {"parts": [{"type": "text", "text": "My name is Ada."}]}
        first = await client.post(
            f"/v1/conversations/{conversation_id}/messages/stream",
            headers=owner_headers("turn-1"),
            json=payload,
        )
        second = await client.post(
            f"/v1/conversations/{conversation_id}/messages/stream",
            headers=owner_headers("turn-1"),
            json=payload,
        )
        messages = await client.get(
            f"/v1/conversations/{conversation_id}",
            headers=owner_headers(),
        )

    assert created.status_code == 200
    assert first.status_code == second.status_code == 200
    assert completed_event(first.text)["message_id"] == completed_event(second.text)["message_id"]
    assert (
        len([message for message in messages.json()["messages"] if message["role"] == "assistant"])
        == 1
    )


@pytest.mark.asyncio
async def test_context_regenerate_and_branch_are_owner_scoped(app_with_db) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app_with_db), base_url="http://test"
    ) as client:
        conversation = await client.post("/v1/conversations", headers=owner_headers())
        conversation_id = conversation.json()["id"]
        response = await client.post(
            f"/v1/conversations/{conversation_id}/messages/stream",
            headers=owner_headers("turn-2"),
            json={"parts": [{"type": "text", "text": "Remember Ada."}]},
        )
        event = completed_event(response.text)
        message_id = event["message_id"]
        context = await client.get(
            f"/v1/conversations/{conversation_id}/context/{message_id}",
            headers=owner_headers(),
        )
        wrong_owner = await client.get(
            f"/v1/conversations/{conversation_id}/context/{message_id}",
            headers={"X-Contextwise-Owner": "wrong-token"},
        )
        regenerated = await client.post(
            f"/v1/messages/{message_id}/regenerate/stream",
            headers=owner_headers("regenerate-1"),
        )
        branch = await client.post(
            f"/v1/messages/{message_id}/branch",
            headers=owner_headers(),
        )

    assert context.status_code == 200
    assert context.json()["snapshot"]["selected_message_ids"]
    assert wrong_owner.status_code == 401
    assert regenerated.status_code == 200
    assert completed_event(regenerated.text)["message_id"] != message_id
    assert branch.status_code == 200
    assert branch.json()["id"] != conversation_id
