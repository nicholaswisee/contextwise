# Contextwise — Solo AI Engineering Project Brief

> **Mission:** Build a production-grade, context-aware personal AI workspace while learning modern AI engineering through deliberate, measurable implementation.

> **Product principle:** One evolving application, not a collection of disconnected tutorials.

> **Learning principle:** Every milestone must produce a working feature, evidence that it works, an engineering reflection, and a measurable improvement over the previous system.

## 1. Product Summary

Contextwise is a private AI workspace that helps a user work with the right context at the right time. It begins as a provider-neutral LLM service and grows into a document assistant, research system, safe tool-using assistant, memory-enabled workspace, repository intelligence tool, MCP server, and experimentation platform.

The application is intentionally a solo side project. Its purpose is not to compete with commercial assistants. Its purpose is to provide a realistic environment in which to learn the engineering disciplines required to build dependable AI systems around probabilistic models.

The project emphasizes:

- reliable model integration rather than one-off API calls;
- evidence-grounded answers rather than plausible text alone;
- explicit workflows before autonomous agents;
- typed boundaries, permissions, and auditability;
- evaluation before optimization;
- observability before operational complexity;
- incremental releases that remain useful on their own.

## 2. The Name

**Contextwise** reflects the central product thesis: model intelligence is not enough. Useful AI systems must assemble, protect, retrieve, rank, compress, and explain context well.

The name also supports a playful identity for a side project. Contextwise can be presented as “the assistant that tries to be wise about context, even when the model is not.”

## 3. Final Product Vision

Contextwise should eventually support six operating modes.

### Assistant Mode

- Multi-turn chat with streaming responses
- Structured response modes
- Image and file input
- Model selection and policy-based routing
- Conversation branching and regeneration
- Traceable prompt and usage metadata

### Knowledge Mode

- Upload and organize documents
- Search by semantics, keywords, metadata, and relationships
- Ask questions across selected collections
- Display exact supporting passages and source locations
- Re-index documents when ingestion settings change

### Research Mode

- Plan a research task
- Search the web and local knowledge
- Retrieve, deduplicate, and assess sources
- Extract claims and evidence
- Produce cited reports
- Save reports and source collections

### Action Mode

- Use typed tools such as calculator, time, search, filesystem, GitHub, and sandboxed Python
- Apply permissions and confirmation requirements
- Record tool inputs, outputs, errors, and authorization decisions
- Enforce time, cost, iteration, and output limits

### Coding Mode

- Index Git repositories
- Explain files, symbols, dependencies, and architecture
- Answer repository questions with file and line citations
- Generate documentation and read-only review suggestions
- Incrementally update indexes by commit

### Laboratory Mode

- Compare prompts, models, embeddings, chunking, rerankers, and routing policies
- Run offline evaluations
- Inspect traces and failures
- Generate reproducible benchmark reports
- Promote tested configurations into production defaults

## 4. What This Project Is Designed to Teach

The roadmap develops four parallel tracks.

1. **Product track:** what Contextwise can do for a user.
2. **AI systems track:** prompting, retrieval, tools, memory, evaluation, routing, and orchestration.
3. **Platform track:** APIs, databases, jobs, storage, observability, security, and deployment.
4. **Learning-evidence track:** tests, benchmarks, ADRs, demos, retrospectives, and release notes.

A milestone is not complete merely because the feature appears to work once. It is complete when all four tracks have produced evidence.

## 5. Scope Boundaries

### In Scope

- LLM application architecture
- Prompt and context engineering
- Structured model outputs
- Retrieval-augmented generation
- Tool calling and controlled orchestration
- Explicit memory architectures
- AI evaluation and observability
- Model routing, fallback, and caching
- Local model serving
- AI security and prompt-injection resistance
- Production APIs and background workers
- MCP interoperability

### Deferred Until the Core Is Mature

- Foundation-model training
- Fine-tuning before an evaluation dataset exists
- General autonomous agents
- Multi-agent orchestration before single-agent workflows are reliable
- Knowledge graphs before hybrid retrieval has been evaluated
- Kubernetes before Docker Compose is operationally insufficient
- A polished consumer frontend before backend behavior is measurable

### Anti-Goals

Contextwise must not become:

- a thin wrapper around an LLM API;
- a showcase of frameworks with no architectural discipline;
- an assistant that can perform consequential actions without safeguards;
- a demo judged only by whether one answer looks impressive;
- a system whose prompts, retrieval, tools, and storage cannot be tested independently.

## 6. Core Technology Strategy

| Area | Primary choice | Learning purpose |
|---|---|---|
| API | FastAPI, Uvicorn | Async APIs, streaming, dependency injection |
| Types/configuration | Pydantic, Pydantic Settings | Validation and typed boundaries |
| Persistence | PostgreSQL, SQLAlchemy, Alembic | Durable state and schema evolution |
| Vector storage | pgvector | Vector search inside a relational system |
| AI application layer | PydanticAI | Typed agents, tools, dependencies, results |
| Provider abstraction | LiteLLM | Provider-neutral model calls and fallback |
| Object storage | Local → MinIO → Cloudflare R2 | Separate metadata from binary content |
| Jobs | In-process → Redis-backed worker | Introduce background work incrementally |
| Observability | OpenTelemetry + Langfuse | Distributed and AI-specific traces |
| Evaluation | Pytest + custom evaluators + DeepEval/Pydantic Evals | Deterministic and probabilistic tests |
| Local inference | Ollama | Operational experience with local models |
| Packaging | uv or Poetry | Reproducible environments |
| Deployment | Docker Compose, optional Kubernetes | Incremental operational complexity |

### Architectural Rule

External frameworks must remain behind Contextwise-owned interfaces. Domain and application code must not be coupled throughout the codebase to provider SDKs.

Examples:

```text
LLMClient        -> LiteLLM adapter
EmbeddingClient  -> cloud/local embedding adapters
ObjectStore      -> local/MinIO/R2 adapters
SearchProvider   -> Exa/other adapters
TraceSink        -> OpenTelemetry/Langfuse adapters
```

## 7. Target Architecture

```text
Web or CLI Client
       |
       v
FastAPI Application
  |-- Conversation API
  |-- Document API
  |-- Research API
  |-- Tool API
  |-- Experiment API
  |-- MCP API
       |
       v
Application Services
  |-- AssistantService
  |-- IngestionService
  |-- RetrievalService
  |-- ResearchService
  |-- ToolExecutionService
  |-- MemoryService
  |-- EvaluationService
       |
       v
AI Runtime
  |-- Prompt Registry
  |-- Context Builder
  |-- Model Router
  |-- Agent Runtime
  |-- Tool Registry
  |-- Guardrails and Policies
       |
       +-----------------------------+
       |              |              |
       v              v              v
PostgreSQL        Object Storage   Worker Queue
+ pgvector        local/MinIO/R2   jobs/evals
       |
       v
External Providers and Local Models
       |
       v
OpenTelemetry -> Langfuse / metrics / logs
```

## 8. Required Architectural Boundaries

- API handlers do not assemble prompts.
- Prompts do not access the database.
- Agents do not instantiate provider clients.
- Retrieval returns evidence objects, not preformatted prompt strings.
- Tool execution passes through policy and authorization checks.
- Evaluations can call application services without using HTTP.
- Trace identifiers propagate across API, model, retrieval, jobs, and tools.
- Untrusted files and code do not execute inside the API process.

## 9. Core Domain Objects

At minimum:

- `User`, `Workspace`
- `Conversation`, `Message`
- `ModelInvocation`, `PromptVersion`
- `Document`, `DocumentVersion`, `DocumentChunk`
- `EmbeddingRecord`, `Collection`
- `RetrievalRun`, `RetrievedEvidence`
- `ToolDefinition`, `ToolExecution`
- `MemoryItem`
- `ResearchRun`, `Source`
- `EvaluationDataset`, `EvaluationCase`, `EvaluationRun`
- `Experiment`, `Feedback`

Every generated answer should be traceable to its prompt version, model configuration, evidence, tool executions, token/cost record, and trace ID.

## 10. Definition of Done for Every Milestone

A milestone is complete only when:

1. The feature works through a public interface such as REST, CLI, or UI.
2. Deterministic logic has unit tests.
3. External boundaries have integration or contract tests.
4. Probabilistic behavior has a small frozen evaluation set.
5. Traces expose latency, usage, retries, failures, and relevant decisions.
6. Error states return useful typed responses.
7. Security and privacy implications are documented.
8. A learning note explains what changed, what failed, and what was learned.
9. A clean checkout can reproduce the demo.
10. All milestone-specific acceptance criteria pass.

## 11. Solo Working Method

For every milestone:

1. Write one or more user scenarios.
2. Define acceptance criteria before implementation.
3. Freeze a small evaluation set.
4. Draw the minimal architecture.
5. Build the smallest vertical slice.
6. Instrument it.
7. Test deterministic behavior.
8. Run behavioral evaluations.
9. Analyze failures and improve one variable at a time.
10. Write a retrospective and tag a reproducible release.

A sustainable rhythm is: **build → test → measure → reflect → ship**.

Use effort bands instead of calendar promises:

- Small: 15–30 focused hours
- Medium: 30–60 focused hours
- Large: 60–100 focused hours

## 12. Release Tiers

### Tier A — Strong Foundation

Milestones 0–5: service foundation, LLM gateway, assistant, ingestion, manual RAG, hybrid retrieval.

**Result:** a credible document assistant and a practical understanding of core AI engineering.

### Tier B — Reliable AI Application

Milestones 6–11: tools, research, memory, observability, evaluation, security.

**Result:** a measurable and defensible AI application rather than a demo.

### Tier C — Optimization and Specialization

Milestones 12–14: local models, routing/caching, coding assistant.

**Result:** experience with inference operations, cost-quality trade-offs, and domain-specific retrieval.

### Tier D — Advanced Interoperability and Research

Milestones 15–19: orchestration, MCP, knowledge graph, production operations, experimentation platform.

**Result:** a long-term AI platform and a portfolio-quality engineering case study.

## 13. Final Graduation Standard

The project is complete when you can:

- explain a request from API entry to final trace;
- replace a model provider without rewriting domain logic;
- diagnose whether a failed answer came from ingestion, retrieval, context construction, generation, or tools;
- demonstrate mechanically traceable citations;
- build a typed tool loop with permissions, budgets, and termination;
- create and maintain evaluation datasets;
- compare candidate changes against frozen baselines;
- restore data, roll back a release, and enforce budgets;
- document trade-offs and rejected alternatives honestly;
- demonstrate not only what was built, but what was learned and measured.

## 14. Document Map

Use `README.md` as the roadmap index. Each file in `milestones/` is an executable work package with tasks, completion evidence, and an exit gate. Use `templates/MILESTONE_RETROSPECTIVE.md` at the end of every milestone.
