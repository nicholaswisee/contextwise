# Parser Fixture 001 Evaluation

**Dataset:** `experiments/parser-fixtures-001/cases.jsonl`
**Result:** `experiments/parser-fixtures-001/results.jsonl`
**Run:** 2026-10-09, local Python 3.12, pypdf 6.19.0

The frozen set has 15 documents: five TXT, five Markdown, and five generated
text PDFs. It includes whitespace changes, headings, Unicode, and source-page
provenance. The runner compares complete extracted text and checks every
segment's source slice after whitespace normalization. It also checks page and
section metadata.

| Format | Documents | Complete extraction | Accurate locations |
|---|---:|---:|---:|
| TXT | 5 | 5 | 5 |
| Markdown | 5 | 5 | 5 |
| PDF | 5 | 5 | 5 |
| **Total** | **15** | **15** | **15** |

Run `uv run python experiments/parser-fixtures-001/runner.py` to regenerate
the result artifact. Latency fields measure local extraction only. The PDF
fixtures are simple digital-text pages generated at run time, so this baseline
does not cover OCR, multi-column reading order, or table structure.
