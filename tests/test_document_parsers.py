import io

import pytest
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

from contextwise.application.ingestion.parsers import ParseError, extract
from contextwise.application.ingestion.service import IngestionService, UploadError
from contextwise.config import Settings
from contextwise.infrastructure.database import Database
from contextwise.infrastructure.documents import DocumentRepository
from contextwise.infrastructure.object_store import LocalObjectStore


def pdf_bytes(text: str) -> bytes:
    stream = io.BytesIO()
    page = canvas.Canvas(stream)
    page.drawString(72, 720, text)
    page.save()
    return stream.getvalue()


def test_markdown_section_and_offsets_survive_normalization() -> None:
    source = "# Alpha\n\n  First   line\nsecond line\n\n# Beta\nThird line\n"
    result = extract(source.encode(), "text/markdown")
    assert [segment.text for segment in result.segments] == ["First line second line", "Third line"]
    assert [segment.section for segment in result.segments] == ["Alpha", "Beta"]
    for segment in result.segments:
        assert segment.text == " ".join(source[segment.start_offset : segment.end_offset].split())


def test_pdf_page_provenance() -> None:
    result = extract(pdf_bytes("Source page text"), "application/pdf")
    assert len(result.segments) == 1
    assert result.segments[0].page == 1
    assert result.segments[0].text == "Source page text"


def test_encrypted_pdf_is_rejected() -> None:
    writer = PdfWriter()
    writer.append_pages_from_reader(PdfReader(io.BytesIO(pdf_bytes("Secret"))))
    writer.encrypt("password")
    stream = io.BytesIO()
    writer.write(stream)
    with pytest.raises(ParseError) as error:
        extract(stream.getvalue(), "application/pdf")
    assert error.value.code == "encrypted_pdf"


@pytest.mark.parametrize(
    ("data", "mime", "code"),
    [
        (b"%PDF-invalid", "application/pdf", "invalid_pdf"),
        (b"\xff", "text/plain", "invalid_utf8"),
        (b" \n\n", "text/plain", "empty_document"),
    ],
)
def test_parser_failures_are_stable(data: bytes, mime: str, code: str) -> None:
    with pytest.raises(ParseError) as error:
        extract(data, mime)
    assert error.value.code == code


def test_upload_rejects_unsafe_inputs_before_storage(tmp_path) -> None:
    settings = Settings(DATABASE_URL="postgresql+asyncpg://user:pass@localhost/test")
    repository = DocumentRepository(Database(settings).session_factory)
    service = IngestionService(repository, LocalObjectStore(str(tmp_path)), 16, 1)
    cases = [
        ("../escape.txt", "text/plain", b"safe", "invalid_filename"),
        ("nul\x00.txt", "text/plain", b"safe", "invalid_filename"),
        ("bad.exe", "application/octet-stream", b"safe", "unsupported_extension"),
        ("fake.pdf", "application/pdf", b"text", "invalid_pdf_signature"),
        ("large.txt", "text/plain", b"x" * 17, "file_too_large"),
        ("binary.txt", "text/plain", b"x\x00y", "binary_text_file"),
        ("wrong.txt", "application/pdf", b"safe", "mime_mismatch"),
    ]
    for filename, mime, data, code in cases:
        with pytest.raises(UploadError) as error:
            service._validate(filename, mime, data)
        assert error.value.code == code
    assert not list(tmp_path.rglob("*"))


def test_object_store_detects_corruption(tmp_path) -> None:
    store = LocalObjectStore(str(tmp_path))
    digest = store.put(b"original")
    assert store.put(b"original") == digest
    assert store.get(digest) == b"original"
    (tmp_path / digest[:2] / digest).write_bytes(b"changed")
    with pytest.raises(ValueError, match="checksum"):
        store.get(digest)
