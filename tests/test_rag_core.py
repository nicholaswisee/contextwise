import httpx
import pytest

from contextwise.application.rag.chunking import ChunkConfig, chunk_segment
from contextwise.application.rag.embeddings import (
    CloudEmbeddingClient,
    EmbeddingError,
    HashEmbeddingClient,
)
from contextwise.application.rag.service import Evidence, select_context, valid_citations


def test_chunk_boundaries_overlap_and_heading_text() -> None:
    text = " ".join(f"word{i}" for i in range(13))
    chunks = chunk_segment(text, "Safety", ChunkConfig(size=8, overlap=3, strategy="heading"))
    assert [chunk.text.split()[0] for chunk in chunks] == ["word0", "word5"]
    assert chunks[0].text.split()[-3:] == chunks[1].text.split()[:3]
    assert text[chunks[0].start_offset : chunks[0].end_offset] == chunks[0].text
    assert chunks[1].embedding_text.startswith("Safety\n")
    assert chunks[1].end_offset == len(text)


def _evidence(number: int, text: str) -> Evidence:
    return Evidence(
        id=str(number),
        citation_id=f"E{number}",
        document_id="doc",
        version_id="version",
        segment_id="segment",
        page=2,
        section="Safety",
        source_start_offset=10,
        source_end_offset=90,
        segment_start_offset=0,
        segment_end_offset=len(text),
        text=text,
        score=0.8,
    )


def test_context_budget_and_citation_integrity() -> None:
    first = _evidence(1, "one two three four")
    second = _evidence(2, "five six seven eight")
    selected = select_context([first, second], 12)
    assert selected == [first]
    assert valid_citations("Supported [E1]", selected)
    assert not valid_citations("Invented [E2]", selected)
    assert not valid_citations("No citation", selected)
    assert not valid_citations("Malformed [E999]", selected)


@pytest.mark.asyncio
async def test_cloud_embedding_retries_and_partial_batch_failure() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429)
        if calls == 3:
            return httpx.Response(400)
        return httpx.Response(200, json={"data": [{"index": 0, "embedding": [1.0] + [0.0] * 255}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = CloudEmbeddingClient("test-model", "secret", batch_size=1, client=client)
        with pytest.raises(EmbeddingError, match="embedding_provider_rejected"):
            await adapter.embed(["first", "second"])
    assert calls == 3


@pytest.mark.asyncio
async def test_hash_embedding_is_repeatable_and_model_specific() -> None:
    first = await HashEmbeddingClient("v1").embed(["oak tree", "oak tree"])
    second = await HashEmbeddingClient("v2").embed(["oak tree"])
    assert first[0] == first[1]
    assert first[0] != second[0]
