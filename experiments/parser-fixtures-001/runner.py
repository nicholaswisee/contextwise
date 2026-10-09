"""Run the frozen 15-document extraction and source-location fixture set."""

import io
import json
import time
from pathlib import Path

from pypdf import PdfReader
from reportlab.pdfgen import canvas

from contextwise.application.ingestion.parsers import extract

ROOT = Path(__file__).parent


def render_pdf(text: str) -> bytes:
    stream = io.BytesIO()
    page = canvas.Canvas(stream)
    page.drawString(72, 720, text)
    page.save()
    return stream.getvalue()


def run() -> list[dict[str, object]]:
    cases = [json.loads(line) for line in (ROOT / "cases.jsonl").read_text().splitlines()]
    results: list[dict[str, object]] = []
    for case in cases:
        source = case["source"]
        kind = case["format"]
        data = render_pdf(source) if kind == "pdf" else source.encode()
        mime = {"txt": "text/plain", "md": "text/markdown", "pdf": "application/pdf"}[kind]
        start = time.perf_counter_ns()
        extraction = extract(data, mime)
        latency_ms = (time.perf_counter_ns() - start) / 1_000_000
        source_text = (
            PdfReader(io.BytesIO(data)).pages[0].extract_text() if kind == "pdf" else source
        )
        source_location_ok = all(
            " ".join(source_text[segment.start_offset : segment.end_offset].split()) == segment.text
            for segment in extraction.segments
        )
        expected_page = case["expected_page"]
        expected_section = case["expected_section"]
        location_ok = source_location_ok and all(
            segment.page == expected_page for segment in extraction.segments
        )
        if expected_section is not None:
            location_ok = location_ok and extraction.segments[-1].section == expected_section
        results.append(
            {
                "id": case["id"],
                "format": kind,
                "extraction_complete": extraction.text == case["expected_text"],
                "location_accurate": location_ok,
                "segment_count": len(extraction.segments),
                "latency_ms": round(latency_ms, 3),
            }
        )
    return results


if __name__ == "__main__":
    rows = run()
    destination = ROOT / "results.jsonl"
    destination.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    print(
        f"{len(rows)} documents; "
        f"{sum(bool(row['extraction_complete']) for row in rows)} complete; "
        f"{sum(bool(row['location_accurate']) for row in rows)} accurate locations"
    )
