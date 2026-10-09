"""Embedding contract, deterministic local baseline, and HTTP cloud adapter."""

import asyncio
import hashlib
import math
import re
from collections.abc import Sequence
from typing import Protocol

import httpx

DIMENSIONS = 256


class EmbeddingError(Exception):
    pass


class EmbeddingClient(Protocol):
    model: str

    async def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


def validate_vectors(vectors: list[list[float]], count: int) -> None:
    if len(vectors) != count:
        raise EmbeddingError("embedding_count_mismatch")
    for vector in vectors:
        if len(vector) != DIMENSIONS or not all(math.isfinite(value) for value in vector):
            raise EmbeddingError("invalid_embedding")
        if not any(vector):
            raise EmbeddingError("zero_embedding")


class HashEmbeddingClient:
    """Reproducible lexical baseline; the cloud adapter provides semantic embeddings."""

    def __init__(self, seed: str = "v1"):
        self.seed = seed
        self.model = f"hash-256-{seed}"

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            values = [0.0] * DIMENSIONS
            terms = re.findall(r"[\w]+", text.casefold())
            for term in terms:
                digest = hashlib.blake2b(f"{self.seed}:{term}".encode(), digest_size=8).digest()
                slot = int.from_bytes(digest[:4], "big") % DIMENSIONS
                values[slot] += 1.0 if digest[4] % 2 == 0 else -1.0
            length = math.sqrt(sum(value * value for value in values))
            if length == 0:
                values[0] = 1.0
            else:
                values = [value / length for value in values]
            vectors.append(values)
        return vectors


class CloudEmbeddingClient:
    """OpenAI-compatible embeddings API with bounded batches and retryable status handling."""

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        batch_size: int = 32,
        max_retries: int = 2,
        client: httpx.AsyncClient | None = None,
    ):
        if not api_key:
            raise ValueError("embedding API key is required")
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.batch_size = batch_size
        self.max_retries = max_retries
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(timeout=30)

    async def aclose(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        result: list[list[float]] = []
        for offset in range(0, len(texts), self.batch_size):
            batch = list(texts[offset : offset + self.batch_size])
            for attempt in range(self.max_retries + 1):
                try:
                    response = await self.client.post(
                        f"{self.base_url}/embeddings",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        json={"model": self.model, "input": batch, "dimensions": DIMENSIONS},
                    )
                except httpx.TransportError as error:
                    if attempt == self.max_retries:
                        raise EmbeddingError("embedding_transport_error") from error
                    await asyncio.sleep(min(0.25 * (2**attempt), 2))
                    continue
                if response.status_code in {429, 500, 502, 503, 504}:
                    if attempt == self.max_retries:
                        raise EmbeddingError("embedding_provider_unavailable")
                    await asyncio.sleep(min(0.25 * (2**attempt), 2))
                    continue
                if response.status_code >= 400:
                    raise EmbeddingError("embedding_provider_rejected")
                try:
                    rows = sorted(response.json()["data"], key=lambda row: row["index"])
                    vectors = [[float(value) for value in row["embedding"]] for row in rows]
                    validate_vectors(vectors, len(batch))
                except (KeyError, TypeError, ValueError) as error:
                    raise EmbeddingError("invalid_embedding_response") from error
                result.extend(vectors)
                break
        return result
