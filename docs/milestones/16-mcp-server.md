# Milestone 16 — MCP Server

**Release target:** `v0.16`  
**Tier:** D  
**Effort band:** Medium  
**Depends on:** Milestone 15 exit gate

## 1. Goal

Expose stable Contextwise capabilities to external AI hosts through a controlled interoperability layer.

## 2. Primary User Story

> As an authorized MCP client, I can discover and use selected Contextwise tools and resources without receiving capabilities or data outside my policy scope.

## 3. Why This Milestone Exists

This milestone is a learning unit, a product release, and an engineering proof point. Do not optimize for feature count. Optimize for a narrow vertical slice that can be demonstrated, tested, measured, and explained.

## 4. What You Should Learn

- protocol transports and lifecycle
- tool, resource, and prompt semantics
- capability discovery
- schema interoperability
- client authentication and authorization
- remote trust boundaries
- protocol-compliant error handling

At the end, you should be able to explain these topics without relying on framework slogans and show where each concept appears in the codebase.

## 5. Required Deliverables

- [ ] MCP server transport
- [ ] tool exposure
- [ ] resource exposure
- [ ] selected prompt templates
- [ ] authentication
- [ ] per-client authorization
- [ ] capability discovery
- [ ] audit logging
- [ ] compatibility tests

## 6. Task Checklist

### 6.1 Design Before Coding

- [ ] Choose local and/or remote transport.
- [ ] Map internal capabilities to MCP tools and resources.
- [ ] Define client identity and scopes.
- [ ] Define error and timeout translation.
- [ ] Define versioning and backward compatibility.

### 6.2 Implementation

- [ ] Implement MCP server initialization and capability discovery.
- [ ] Expose document search and passage retrieval.
- [ ] Expose saved reports and repository indexes as resources.
- [ ] Expose bounded research workflow and approved memory operations as tools.
- [ ] Map schemas to internal contracts.
- [ ] Enforce client authorization before discovery and execution.
- [ ] Propagate MCP requests into traces and audit logs.
- [ ] Test selected clients.

### 6.3 Deterministic and Integration Tests

- [ ] Unauthorized client.
- [ ] Client with partial scopes.
- [ ] Malformed tool arguments.
- [ ] Server timeout.
- [ ] Internal error translation.
- [ ] Capability removed or version changed.
- [ ] Cross-workspace resource attempt.
- [ ] Concurrent clients.

### 6.4 Behavioral Evaluation and Measurement

- [ ] Create interoperability scenarios for each supported client.
- [ ] Measure schema compatibility, task completion, error clarity, authorization correctness, and trace coverage.

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

- [ ] Clients discover only authorized capabilities.
- [ ] MCP schemas match internal contracts or use explicit adapters.
- [ ] Every external action appears in traces and audit logs.
- [ ] Failures return protocol-compliant errors.
- [ ] At least two selected clients complete the compatibility suite.

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

- [ ] `docs/learning/16-mcp.md`
- [ ] MCP capability catalog
- [ ] compatibility report
- [ ] client configuration examples
- [ ] tag `contextwise-v0.16-mcp`

Also attach or link:

- [ ] one successful trace;
- [ ] one representative failure trace;
- [ ] benchmark or evaluation output;
- [ ] release notes describing user-visible and architectural changes;
- [ ] open issues for consciously deferred work.

## 10. Suggested Demo Script

1. Connect a supported client.
2. Discover capabilities.
3. Search Contextwise documents.
4. Run an authorized tool.
5. Show a denied capability and the corresponding audit event.


## 11. Reflection Questions

- Which internal abstractions mapped poorly to MCP?
- How does remote exposure change the threat model?
- What should be a resource instead of a tool?

Write answers in the learning note. The point is not to produce polished theory. The point is to record what your implementation taught you that documentation alone did not.

## 12. Exit Gate

Before starting Milestone 17, verify:

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
