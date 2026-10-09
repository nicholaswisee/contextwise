"""Pure extraction with locations in the original decoded page or file text."""

import io
import re
from dataclasses import dataclass

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class ParseError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class Segment:
    text: str
    page: int | None
    section: str | None
    start_offset: int
    end_offset: int


@dataclass(frozen=True)
class Extraction:
    text: str
    segments: tuple[Segment, ...]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _paragraphs(text: str, page: int | None, markdown: bool) -> list[Segment]:
    segments: list[Segment] = []
    section: str | None = None
    start: int | None = None
    end = 0

    def flush() -> None:
        nonlocal start
        if start is not None:
            cleaned = _normalize(text[start:end])
            if cleaned:
                segments.append(Segment(cleaned, page, section, start, end))
        start = None

    offset = 0
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if not stripped:
            flush()
        elif markdown and re.match(r"^#{1,6}\s", stripped):
            flush()
            section = stripped.lstrip("# ").strip()[:255]
        else:
            if start is None:
                start = offset + len(line) - len(line.lstrip())
            end = offset + len(line.rstrip())
        offset += len(line)
    flush()
    return segments


def extract(data: bytes, mime_type: str) -> Extraction:
    if mime_type in {"text/plain", "text/markdown"}:
        try:
            raw_text = data.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise ParseError("invalid_utf8") from error
        segments = _paragraphs(raw_text, None, mime_type == "text/markdown")
    elif mime_type == "application/pdf":
        try:
            reader = PdfReader(io.BytesIO(data), strict=True)
            if reader.is_encrypted:
                raise ParseError("encrypted_pdf")
            if len(reader.pages) > 200:
                raise ParseError("too_many_pages")
            segments = []
            for page_number, page in enumerate(reader.pages, start=1):
                segments.extend(_paragraphs(page.extract_text() or "", page_number, False))
        except (PdfReadError, ValueError, IndexError, KeyError) as error:
            raise ParseError("invalid_pdf") from error
    else:
        raise ParseError("unsupported_mime")

    if not segments:
        raise ParseError("empty_document")
    return Extraction("\n\n".join(segment.text for segment in segments), tuple(segments))
