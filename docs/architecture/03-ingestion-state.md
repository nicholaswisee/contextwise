# Milestone 3 — Ingestion State and Provenance

```mermaid
flowchart LR
  Owner --> Document
  Document --> Version
  Version --> Object[Original SHA-256 object]
  Version --> Segment[Extracted segment]
  Version --> Job[Ingestion job]
  Job --> Pending
  Pending --> Processing
  Processing --> Completed
  Processing --> Failed
  Processing --> Cancelled
  Failed --> Pending
  Cancelled --> Pending
  Completed --> Reprocess[New reprocess job]
  Reprocess --> Pending
```

Each segment has an ordinal, optional PDF page, optional Markdown section, and
character offsets into the raw extracted page or decoded source text. The
normalized segment text and full extracted text are database data; the
content-addressed object is the unmodified original upload.
