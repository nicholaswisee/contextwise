# Milestone 6 — Safe Tool-Calling Runtime

**Release target:** `v0.6`  
**Tier:** B  
**Effort band:** Large  
**Depends on:** Milestone 5 exit gate

## 1. Goal

Build a typed, permission-aware runtime that lets models request actions without letting model intent become authorization.

## 2. Primary User Story

> As a user, I can let Contextwise use approved tools, see what it intends to do, confirm consequential actions, and inspect a complete execution audit trail.

## 3. Why This Milestone Exists

This milestone is a learning unit, a product release, and an engineering proof point. Do not optimize for feature count. Optimize for a narrow vertical slice that can be demonstrated, tested, measured, and explained.

## 4. What You Should Learn

- function calling and tool schemas
- tool-selection prompting
- agent-loop mechanics
- authorization versus model intent
- timeouts, retries, and result limits
- prompt-injection boundaries
- iteration, cost, and termination budgets

At the end, you should be able to explain these topics without relying on framework slogans and show where each concept appears in the codebase.

## 5. Required Deliverables

- [ ] tool registry
- [ ] versioned input/output schemas
- [ ] tool metadata and permission levels
- [ ] execution service
- [ ] timeouts and error taxonomy
- [ ] confirmation gate
- [ ] audit log
- [ ] result-size limits
- [ ] tool-loop budgets
- [ ] initial safe tools

## 6. Task Checklist

### 6.1 Design Before Coding

- [ ] Define `safe_read`, `sensitive_read`, `reversible_write`, and `irreversible_write`.
- [ ] Define tool lifecycle: proposed, authorized, running, completed, failed, denied.
- [ ] Specify confirmation payloads and expiry.
- [ ] Define maximum calls, cost, duration, and result size.
- [ ] Define how untrusted tool output is marked in context.

### 6.2 Implementation

- [ ] Implement typed `ToolDefinition` and `ToolExecution`.
- [ ] Build registry and dependency injection.
- [ ] Implement calculator and current-time tools.
- [ ] Implement read-only filesystem and Markdown reader.
- [ ] Add weather, web search, and GitHub read adapters.
- [ ] Add sandboxed Python with strict resource limits.
- [ ] Implement policy checks before every execution.
- [ ] Implement confirmation for write-capable test tools.
- [ ] Feed typed errors back to the model.
- [ ] Persist audit events and trace spans.
- [ ] Prevent repeated identical calls and infinite loops.

### 6.3 Deterministic and Integration Tests

- [ ] Model requests an unknown tool.
- [ ] Invalid tool arguments.
- [ ] Permission denied.
- [ ] Confirmation rejected or expired.
- [ ] Tool timeout.
- [ ] Oversized tool result.
- [ ] Prompt-injected document requests a forbidden action.
- [ ] Repeated tool loop.
- [ ] Tool output attempts to override system policy.
- [ ] Workspace attempts to access another workspace tool resource.

### 6.4 Behavioral Evaluation and Measurement

- [ ] Create at least 25 tool-use cases with expected tool, arguments, and prohibited actions.
- [ ] Measure selection accuracy, argument validity, task completion, unnecessary calls, latency, and safety violations.

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

- [ ] The model cannot bypass policy checks.
- [ ] All tool calls have typed arguments and results.
- [ ] Consequential actions require explicit confirmation.
- [ ] Infinite loops are stopped by deterministic budgets.
- [ ] Tool output is labeled and treated as untrusted.
- [ ] Every proposal, denial, execution, and error is traceable.

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

- [ ] `docs/learning/06-tool-runtime.md`
- [ ] tool policy specification
- [ ] tool-use evaluation dataset
- [ ] prompt-injection test report
- [ ] tag `contextwise-v0.6-tools`

Also attach or link:

- [ ] one successful trace;
- [ ] one representative failure trace;
- [ ] benchmark or evaluation output;
- [ ] release notes describing user-visible and architectural changes;
- [ ] open issues for consciously deferred work.

## 10. Suggested Demo Script

1. Ask a question requiring calculator and time tools.
2. Show automatic execution of safe reads.
3. Trigger a confirmation-required action.
4. Reject it.
5. Demonstrate a blocked injected instruction.


## 11. Reflection Questions

- Why is tool selection not authorization?
- Which failures belong to the model and which to the runtime?
- What tool capabilities should never be exposed to the model?

Write answers in the learning note. The point is not to produce polished theory. The point is to record what your implementation taught you that documentation alone did not.

## 12. Exit Gate

Before starting Milestone 7, verify:

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
