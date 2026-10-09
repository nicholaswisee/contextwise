"""Whitespace-token chunking with offsets relative to an extracted segment."""

import re
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ChunkConfig(BaseModel):
    size: int = Field(default=40, ge=8, le=512)
    overlap: int = Field(default=4, ge=0, le=256)
    strategy: Literal["fixed", "heading"] = "fixed"

    @model_validator(mode="after")
    def valid_overlap(self) -> "ChunkConfig":
        if self.overlap >= self.size:
            raise ValueError("overlap must be smaller than size")
        return self


@dataclass(frozen=True)
class Chunk:
    ordinal: int
    text: str
    embedding_text: str
    start_offset: int
    end_offset: int


def chunk_segment(text: str, section: str | None, config: ChunkConfig) -> tuple[Chunk, ...]:
    tokens = list(re.finditer(r"\S+", text))
    if not tokens:
        return ()
    result: list[Chunk] = []
    stride = config.size - config.overlap
    for ordinal, start in enumerate(range(0, len(tokens), stride)):
        end = min(start + config.size, len(tokens))
        beginning = tokens[start].start()
        ending = tokens[end - 1].end()
        passage = text[beginning:ending]
        embedding_text = (
            f"{section}\n{passage}" if config.strategy == "heading" and section else passage
        )
        result.append(Chunk(ordinal, passage, embedding_text, beginning, ending))
        if end == len(tokens):
            break
    return tuple(result)
