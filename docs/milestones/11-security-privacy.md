# Milestone 11 — Security, Privacy, and AI Abuse Resistance

**Release target:** `v0.11`  
**Tier:** B  
**Effort band:** Large  
**Depends on:** Milestone 10 exit gate

## 1. Goal

Harden the application before increasing autonomy, data retention, or external exposure.

## 2. Primary User Story

> As a user and operator, I can trust that workspaces remain isolated, prompts cannot authorize tools, expensive workflows are bounded, and retained data can be inspected and deleted.

## 3. Why This Milestone Exists

This milestone is a learning unit, a product release, and an engineering proof point. Do not optimize for feature count. Optimize for a narrow vertical slice that can be demonstrated, tested, measured, and explained.

## 4. What You Should Learn

- AI threat modeling
- prompt injection and indirect injection
- authorization and workspace isolation
- malicious file and code isolation
- denial-of-wallet controls
- secret and PII handling
- retention, deletion, and auditability

At the end, you should be able to explain these topics without relying on framework slogans and show where each concept appears in the codebase.

## 5. Required Deliverables

- [ ] formal threat model
- [ ] authentication and workspace authorization
- [ ] rate limits and quotas
- [ ] input/output limits
- [ ] tool allowlists
- [ ] network restrictions
- [ ] sandbox isolation
- [ ] trace/log redaction
- [ ] secret management
- [ ] retention and deletion workflows
- [ ] security event audit trail

## 6. Task Checklist

### 6.1 Design Before Coding

- [ ] Map assets, actors, entry points, trust boundaries, and abuse cases.
- [ ] Create attack trees for prompt injection, exfiltration, poisoned memory, and denial of wallet.
- [ ] Define workspace authorization centrally.
- [ ] Define per-feature budgets and quotas.
- [ ] Define retention and deletion guarantees.

### 6.2 Implementation

- [ ] Implement authentication appropriate to deployment.
- [ ] Enforce workspace checks in repositories and retrieval queries.
- [ ] Add rate limits and request budgets.
- [ ] Limit context, upload, tool, loop, and output sizes.
- [ ] Restrict tool network domains.
- [ ] Move untrusted parsing and code execution outside the API process.
- [ ] Redact secrets and sensitive content before telemetry export.
- [ ] Add secret storage and rotation documentation.
- [ ] Implement delete/export workflows.
- [ ] Record security-relevant denials and policy changes.

### 6.3 Deterministic and Integration Tests

- [ ] Cross-workspace document retrieval.
- [ ] Cross-workspace conversation access.
- [ ] Document and webpage prompt injection.
- [ ] Tool credential exfiltration attempt.
- [ ] Poisoned memory.
- [ ] Malicious upload.
- [ ] Sandbox escape assumptions.
- [ ] Excessive loop and expensive request.
- [ ] Secret leakage in traces.
- [ ] Deletion completeness.

### 6.4 Behavioral Evaluation and Measurement

- [ ] Maintain an adversarial suite and run it against each relevant release.
- [ ] Record exploit success rate, blocked requests, false positives, cost ceilings, and residual risks.

### 6.5 Documentation and Cleanup

- [ ] Update the architecture diagram if boundaries changed.
- [ ] Add or revise Architecture Decision Records for consequential choices.
- [ ] Update API or CLI documentation.
- [ ] Add a migration or upgrade note when persistent data changed.
- [ ] Record known limitations and deferred work.
- [ ] Complete the milestone retrospective template.
- [ ] Prepare a clean-checkout demo script.
- [ ] Tag the release only after the exit gate passes.

## 7. Acceptance Criteria

- [ ] Cross-workspace tests fail closed.
- [ ] Prompt injection cannot directly authorize restricted tools.
- [ ] Credentials never enter model context.
- [ ] Expensive workflows have enforceable budgets.
- [ ] Untrusted execution is isolated from the API process.
- [ ] Users can export and delete their data according to documented policy.
- [ ] Residual risks are explicitly recorded.

## 8. How to Know the Milestone Is Complete

Consider this milestone complete only when all of the following statements are true:

1. **It works:** the user story succeeds through a documented public interface.
2. **It is repeatable:** a clean checkout can reproduce the result.
3. **It is tested:** deterministic behavior and external boundaries have automated coverage.
4. **It is measured:** a frozen evaluation or benchmark exists for probabilistic behavior.
5. **It is observable:** a failure can be located using logs, traces, metrics, and persisted records.
6. **It is bounded:** security, privacy, cost, timeout, and failure implications are documented.
7. **It is explainable:** you can describe why the architecture exists and which alternatives were rejected.
8. **It improves the system:** the result is compared with a prior baseline or establishes the first baseline.
9. **It leaves evidence:** the required artifacts below are committed.
10. **The exit gate passes:** there are no unchecked acceptance criteria classified as required.

A feature that merely works in one manual demonstration does **not** complete the milestone.

## 9. Required Evidence

- [ ] `docs/threat-models/contextwise-v1.md`
- [ ] `docs/learning/11-security.md`
- [ ] adversarial evaluation report
- [ ] data-flow and trust-boundary diagram
- [ ] tag `contextwise-v0.11-security`

Also attach or link:

- [ ] one successful trace;
- [ ] one representative failure trace;
- [ ] benchmark or evaluation output;
- [ ] release notes describing user-visible and architectural changes;
- [ ] open issues for consciously deferred work.

## 10. Suggested Demo Script

1. Attempt cross-workspace access.
2. Run a prompt-injection fixture.
3. Show a tool denial.
4. Trigger a budget limit.
5. Delete a document and verify inaccessible derivatives.


## 11. Reflection Questions

- Which controls must be deterministic?
- What security claims cannot be proven by tests alone?
- Which observability data creates new privacy risk?

Write answers in the learning note. The point is not to produce polished theory. The point is to record what your implementation taught you that documentation alone did not.

## 12. Exit Gate

Before starting Milestone 12, verify:

- [ ] All required deliverables are complete or explicitly removed through an ADR.
- [ ] All acceptance criteria pass.
- [ ] Required tests pass locally and in CI.
- [ ] The behavioral evaluation has a stored baseline.
- [ ] The demo works from a clean environment.
- [ ] Security and privacy review is complete.
- [ ] The learning note and retrospective are committed.
- [ ] The release tag exists and points to the evaluated commit.

**Decision:** `PASS / PASS WITH DOCUMENTED DEBT / FAIL`

A “pass with documented debt” is acceptable only for non-critical scope. It is not acceptable for data isolation, authorization, citation integrity, destructive actions, secrets, or unrecoverable migrations.
