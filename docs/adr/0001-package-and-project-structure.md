# ADR-0001: Package and Project Structure

**Status:** Accepted  
**Date:** 2026-08-04  
**Milestone:** 0

## Context

Milestone 0 requires a reproducible Python environment: package manager, virtualenv, dependency locking, and a pinned interpreter. The project brief lists "uv or Poetry" as the primary packaging choice and leaves the decision to an ADR. No code exists yet, so this decision is being made before the first `pyproject.toml` is written.

Evidence: the dev machine has `uv 0.12.1` installed and no Poetry; Poetry would be a new installation.

## Decision Drivers

- operational complexity (fewest moving parts);
- maintainability (lockfiles, reproducible installs);
- interoperability (works with Docker, Make, CI);
- learning value (the brief's stated reason for choosing deliberately).

## Considered Options

### Option A: uv

Rust-based package manager from Astral. Resolves and locks dependencies, manages virtualenvs and Python versions in one tool, and is installable as a single binary.

### Option B: Poetry

Mature Python-first tool with built-in `pyproject.toml` handling, dependency groups, and a publish workflow. Heavier runtime and slower resolution than uv.

### Option C: pip + venv + requirements.txt

Standard-library approach with no extra tooling. Loses reproducible dependency locking (unless combined with `pip-tools`) and adds manual Python-version management.

## Decision

**Use uv** for package management, virtualenvs, and the pinned Python interpreter.

Scope: this decision covers project tooling only. Application structure (API/application/domain/infrastructure package boundaries) is defined by Milestone 0 §6.1 and will be recorded separately as the codebase takes shape. Developer commands run through `make`, which invokes `uv` internally (`uv sync`, `uv run`).

## Consequences

### Positive

- One tool manages interpreter, virtualenv, and dependencies.
- Fast resolution and installs; trivial CI integration.
- Standard `pyproject.toml` + `uv.lock` — nothing proprietary.
- Already installed on the dev machine; zero setup cost.

### Negative

- Poetry-specific features (publish workflow, `poetry add` conventions) are unavailable — not needed for this project.
- uv is younger than Poetry; the ecosystem around it is still settling.

### Risks

- Lockfile/version skew between `uv.lock` and tools that expect Poetry-style metadata — mitigated because all commands route through `make` + `uv`.

## Exit Strategy

To replace uv with Poetry or pip-tools: delete `uv.lock` and `.venv`, regenerate the environment from `pyproject.toml` with the new tool, and update the `make` recipes. Dependency constraints live in `pyproject.toml`, so no application code changes.

## Validation

- Milestone 0 acceptance: "a clean environment can apply all migrations successfully" and "one documented command runs all local checks" both pass using `uv`-backed `make` recipes.
- CI runs the same lint, type, test, and migration checks through `uv`.
- A fresh `uv sync` on a clean checkout installs a working environment with no manual steps.
