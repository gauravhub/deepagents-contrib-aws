# SDK Integration Checklist: AgentCore Code Interpreter Sandbox

**Purpose**: Validate completeness, clarity, and consistency of requirements for the AgentCore sandbox backend integration
**Created**: 2026-03-22
**Feature**: [spec.md](../spec.md)

## Requirement Completeness

- [ ] CHK001 - Are all four `BaseSandbox` abstract members (`execute`, `id`, `upload_files`, `download_files`) explicitly addressed in requirements? [Completeness, Spec §FR-001]
- [ ] CHK002 - Are requirements for the `executeCommand` response format documented, or is the assumption that it matches `executeCode` format validated? [Completeness, Assumption]
- [ ] CHK003 - Are path normalization requirements defined for `writeFiles` (which requires relative paths) when callers pass absolute paths? [Gap]
- [ ] CHK004 - Are requirements for binary vs text detection in `upload_files` specified with a concrete detection strategy? [Completeness, Spec §FR-009]
- [ ] CHK005 - Is the `integration_source` parameter for `CodeInterpreter` constructor documented in requirements (telemetry tracking)? [Gap]
- [ ] CHK006 - Are requirements defined for what happens when `stop()` itself throws an exception from the AgentCore SDK? [Gap, Spec §FR-007]

## Requirement Clarity

- [ ] CHK007 - Is "session timeout gracefully" (FR-015) specified with concrete detection criteria — what exception/error code indicates a timed-out session? [Clarity, Spec §FR-015]
- [ ] CHK008 - Is the retry strategy for session timeout quantified — how many retries, with what backoff? [Clarity, Spec §FR-015]
- [ ] CHK009 - Is "text and binary content appropriately" (FR-009, FR-010) defined with specific rules for when to use `text` vs `blob` fields? [Clarity, Spec §FR-009]
- [ ] CHK010 - Is the Python extraction regex for `python3 -c "..."` specified with enough detail to handle edge cases (nested quotes, multiline)? [Clarity, Spec §FR-002]
- [ ] CHK011 - Is "max 28800" for `session_timeout_seconds` specified as a validation rule (reject at construction) or advisory? [Clarity, Spec §FR-017]

## Requirement Consistency

- [ ] CHK012 - Are env var precedence rules in FR-013 consistent with the from_env contract in `contracts/public-api.md`? [Consistency, Spec §FR-013]
- [ ] CHK013 - Is the `from_env()` signature consistent between spec (no explicit kwargs listed) and plan (kwargs with `| None` defaults)? [Consistency]
- [ ] CHK014 - Are the `FileOperationError` codes in FR-012 consistent with those actually returned by the upstream `deepagents` protocol? [Consistency, Spec §FR-012]
- [ ] CHK015 - Is the sandbox ID format consistent between the data model (`agentcore-ci-{uuid8}`) and the `id` property behavior (which appends session_id)? [Consistency]

## Acceptance Criteria Quality

- [ ] CHK016 - Are acceptance scenarios for `executeCommand` sufficient — do they cover commands with pipes, redirects, and multi-line output? [Coverage, Spec §US-2]
- [ ] CHK017 - Can SC-001 ("variable state preserved") be objectively measured without implementation knowledge? [Measurability, Spec §SC-001]
- [ ] CHK018 - Are acceptance criteria defined for the lazy import behavior in `__init__.py` when `bedrock-agentcore` is not installed? [Gap, Spec §US-6]

## Scenario Coverage

- [ ] CHK019 - Are requirements defined for concurrent `execute()` calls on the same sandbox instance (thread safety)? [Coverage, Gap]
- [ ] CHK020 - Are requirements defined for re-using a sandbox after `stop()` has been called (can a new session be started)? [Coverage, Gap]
- [ ] CHK021 - Are requirements specified for what happens when `upload_files` receives an empty list? [Coverage, Edge Case]
- [ ] CHK022 - Are requirements defined for commands that produce no output (empty stdout/stderr)? [Coverage, Spec §FR-002]

## Edge Case Coverage

- [ ] CHK023 - Is behavior defined for `execute("python3 -c")` (python3 -c with no code argument)? [Edge Case, Spec §FR-002]
- [ ] CHK024 - Is behavior defined for very large file uploads/downloads approaching memory limits? [Edge Case, Gap]
- [ ] CHK025 - Are requirements defined for `from_env()` when `AGENTCORE_SESSION_TIMEOUT` contains a non-numeric value? [Edge Case, Spec §FR-018]
- [ ] CHK026 - Is behavior defined when `readFiles` returns a response with missing `resource` fields? [Edge Case, Gap]

## Dependencies & Assumptions

- [ ] CHK027 - Is the assumption that `bedrock-agentcore` is available on PyPI validated with a specific minimum version requirement? [Assumption]
- [ ] CHK028 - Is the assumption that `executeCommand` shares the same response format as `executeCode` validated against SDK documentation? [Assumption]
- [ ] CHK029 - Are the `deepagents>=0.4.0` imports (`BaseSandbox`, `ExecuteResponse`, `FileUploadResponse`, `FileDownloadResponse`, `FileOperationError`) verified as available in the installed version? [Dependency, Spec §Assumptions]
- [ ] CHK030 - Is the `bedrock-agentcore` dev dependency version pinned or left unpinned, and is this decision documented? [Dependency]

## Notes

- Check items off as completed: `[x]`
- Items reference spec sections where applicable; `[Gap]` indicates missing requirements
- Focus: SDK integration quality, protocol compliance, dependency management
- Depth: Standard | Audience: Reviewer (PR) | Timing: Pre-implementation
