# Tasks: AgentCore Code Interpreter Sandbox

**Input**: Design documents from `/specs/002-agentcore-sandbox/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/public-api.md

**Tests**: Included — the spec explicitly requires unit tests with mocked CodeInterpreter and integration tests.

**Organization**: Tasks grouped by user story. US1 and US2 share `execute()` in the same file, so they are combined into one phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Package configuration and test infrastructure

<!-- sequential -->
- [x] T001 Update pyproject.toml: add `[project.optional-dependencies] agentcore = ["bedrock-agentcore"]`, add `"bedrock-agentcore"` to dev dependency group, add integration test marker for agentcore sandbox in pyproject.toml

<!-- sequential (T003 imports AgentCoreCodeInterpreterSandbox which doesn't exist until T004) -->
- [x] T002 Create tests/agentcore_sandbox/__init__.py (empty)
- [x] T003 Create tests/agentcore_sandbox/conftest.py with fixtures: `aws_env` (monkeypatch 4 AWS env vars matching s3_backend pattern — `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_DEFAULT_REGION`), `mock_code_interpreter` (mock `CodeInterpreter` class with `start()` returning session ID, `invoke()` returning configurable responses, `stop()` returning True), `sandbox` (pre-configured `AgentCoreCodeInterpreterSandbox` instance with mocked client). **Note**: conftest imports the sandbox class — will only work after T004 completes.

**Checkpoint**: Project configured, test infrastructure ready

---

## Phase 2: Foundational (Core Class Skeleton)

**Purpose**: Create the class skeleton with constructor, properties, and lifecycle methods — MUST complete before user story work

<!-- sequential -->
- [x] T004 Create src/deepagents_contrib_aws/agentcore_sandbox.py with: `_extract_python_from_command()` helper (regex parsing `python3 -c "..."` and `python3 -c '...'` with backslash-escaped quote handling — port from reference at `/home/dhamijag/playground/deep-agents/sdk/hello_world/agentcore_sandbox.py`), `AgentCoreCodeInterpreterSandbox` class extending `BaseSandbox` with constructor (`region_name="us-west-2"`, `session_timeout_seconds=900`, `max_output_chars=100_000`, `code_interpreter_identifier="aws.codeinterpreter.v1"`), `id` property (returns `agentcore-ci-{session_id[:8]}` if session active, else `_sandbox_id`), `_ensure_session()` (lazy init — creates `CodeInterpreter(region, integration_source="deepagents")`, calls `start(identifier, session_timeout_seconds=timeout)`), `stop()` method, `__enter__`/`__exit__` context manager, stub `execute()` returning `ExecuteResponse(output="not implemented", exit_code=1)`, stub `upload_files()` and `download_files()`. Import `CodeInterpreter` with `try/except ImportError`. All code formatted to ruff line-length 88.

**Checkpoint**: Class skeleton compiles, can be imported, stubs in place

---

## Phase 3: User Story 1+2 — Execute Python & Shell Commands (Priority: P1) 🎯 MVP

**Goal**: Implement `execute()` supporting both `python3 -c "..."` (via `executeCode`) and arbitrary shell commands (via `executeCommand`), with output parsing, truncation, and error wrapping.

**Independent Test**: Create sandbox, call `execute('python3 -c "print(42)"')` and `execute("echo hello")`, verify correct output and exit codes.

### Tests for US1+US2

<!-- sequential -->
- [x] T005 [US1][US2] Create tests/agentcore_sandbox/test_execute.py with tests: `test_python_code_execution` (mock `invoke("executeCode")` returning stream with text output, verify `ExecuteResponse(output="42", exit_code=0)`), `test_python_variable_state_preserved` (two consecutive execute calls, second reads variable from first), `test_python_error_returns_exit_code_1` (mock stream with error content, verify exit_code=1), `test_shell_command_execution` (non-python3 command routes to `invoke("executeCommand")`, verify output), `test_shell_command_error` (shell command failure returns exit_code=1), `test_python_extraction_routing` (`python3 -c "..."` → executeCode, `echo hello` → executeCommand), `test_extract_python_single_quotes` (`python3 -c '...'` with single quotes extracted correctly), `test_extract_python_no_argument` (`python3 -c` with no code → falls through to executeCommand), `test_extract_python_nested_quotes` (`python3 -c "print(\"hello\")"` with escaped quotes extracted correctly), `test_output_truncation` (output exceeding max_output_chars is truncated with notice, truncated=True), `test_empty_output` (no output returns `"<no output>"`), `test_empty_command` (empty string passed to executeCommand, error wrapped in ExecuteResponse), `test_mixed_text_and_error_output` (stream with both text and error items, all collected, exit_code=1), `test_sdk_exception_wrapped` (any exception from invoke() wrapped in ExecuteResponse with exit_code=1), `test_lazy_session_init` (session not started until first execute), `test_session_timeout_recovery` (first invoke raises exception, session re-created, retry succeeds). All tests use mocked CodeInterpreter from conftest.

### Implementation for US1+US2

<!-- sequential -->
- [x] T006 [US1][US2] Implement `execute()` in src/deepagents_contrib_aws/agentcore_sandbox.py: call `_ensure_session()`, use `_extract_python_from_command()` to detect python3 -c commands, route to `invoke("executeCode", {"language": "python", "code": extracted_code})` or `invoke("executeCommand", {"command": command})`. Parse response: iterate `response["stream"]` events, collect `result.content[]` items — `type: "text"` → append to output, `type: "error"` → append to output + set exit_code=1. Join output parts with `\n`, default to `"<no output>"` if empty. Apply truncation at `max_output_chars` with notice. Wrap all exceptions in `ExecuteResponse(output=error_msg, exit_code=1, truncated=False)`. Add session timeout recovery: on `Exception` from `invoke()`, log the original exception, try `stop()` + `_ensure_session()` + retry once; if retry also fails, return error response. Use `logging.getLogger(__name__)` for debug logging of retry attempts.

**Checkpoint**: execute() works for both Python and shell commands — all test_execute.py tests pass

---

## Phase 4: User Story 3 — Upload and Download Files (Priority: P2)

**Goal**: Implement `upload_files()` and `download_files()` using native AgentCore `writeFiles`/`readFiles` APIs with text/binary handling and per-file error reporting.

**Independent Test**: Upload text and binary files, download them back, verify content matches.

### Tests for US3

<!-- sequential -->
- [x] T007 [US3] Create tests/agentcore_sandbox/test_files.py with tests: `test_upload_text_file` (mock `invoke("writeFiles")`, verify called with `{"content": [{"path": "relative/path", "text": "content"}]}`), `test_upload_binary_file` (verify binary content sent as base64 blob), `test_upload_multiple_files` (batch upload, verify all responses returned), `test_upload_error_handling` (mock invoke raising exception for one file, verify `FileUploadResponse(error="permission_denied")`), `test_download_text_file` (mock `invoke("readFiles")` returning stream with `resource.text`, verify content as bytes), `test_download_binary_file` (mock response with `resource.blob` base64, verify decoded bytes), `test_download_file_not_found` (mock error response, verify `FileDownloadResponse(error="file_not_found")`), `test_download_multiple_files` (batch download with mixed success/failure), `test_path_normalization` (absolute paths stripped of leading `/` before sending to writeFiles/readFiles), `test_upload_empty_list` (empty list returns empty list), `test_upload_invalid_path` (null bytes in path → `error="invalid_path"`).

### Implementation for US3

<!-- sequential -->
- [x] T008 [US3] Implement `upload_files()` in src/deepagents_contrib_aws/agentcore_sandbox.py: call `_ensure_session()`, for each `(path, content)` tuple: strip leading `/` from path, try UTF-8 decode — if succeeds use `{"path": rel_path, "text": decoded}`, else use `{"path": rel_path, "blob": base64.b64encode(content).decode()}`. Call `invoke("writeFiles", {"content": [file_entry]})` per file. Catch exceptions per-file, map to `FileUploadResponse` with appropriate `FileOperationError`. Return list of responses.

- [x] T009 [US3] Implement `download_files()` in src/deepagents_contrib_aws/agentcore_sandbox.py: call `_ensure_session()`, for each path: strip leading `/`, call `invoke("readFiles", {"paths": [rel_path]})`. Parse response `stream[].result.content[]` — find `type: "resource"` items, extract `resource.text` (encode to bytes) or `resource.blob` (base64 decode). Catch exceptions per-file, map to `FileDownloadResponse` with appropriate `FileOperationError`. Return list of responses.

**Checkpoint**: File upload/download works with text, binary, and error cases — all test_files.py tests pass

---

## Phase 5: User Story 4+5 — Configuration & Lifecycle (Priority: P2)

**Goal**: Implement `from_env()` factory with env var precedence and validate lifecycle management (lazy init, stop, context manager, session timeout).

**Independent Test**: Set env vars, call `from_env()`, verify config. Create sandbox with context manager, verify stop() called on exit.

### Tests for US4+US5

<!-- sequential -->
- [x] T010 [US4][US5] Create tests/agentcore_sandbox/test_lifecycle.py with tests: `test_from_env_agentcore_region` (set `AGENTCORE_REGION`, verify used), `test_from_env_aws_region_fallback` (no AGENTCORE_REGION, set `AWS_REGION`, verify used), `test_from_env_aws_default_region_fallback` (no AGENTCORE/AWS_REGION, set `AWS_DEFAULT_REGION`), `test_from_env_default_region` (no env vars → `us-west-2`), `test_from_env_timeout` (set `AGENTCORE_SESSION_TIMEOUT=3600`), `test_from_env_identifier` (set `AGENTCORE_CODE_INTERPRETER_ID`), `test_from_env_kwargs_override` (kwargs take precedence over env vars), `test_from_env_invalid_timeout` (non-numeric timeout → ValueError), `test_from_env_timeout_exceeds_max` (timeout > 28800 → ValueError), `test_stop_releases_session` (verify client.stop() called, _client set to None), `test_stop_no_session` (stop() before any execute — no error), `test_stop_twice` (stop() called twice — no error), `test_context_manager` (verify stop() called on __exit__), `test_context_manager_exception` (stop() called even if exception in with block), `test_unique_sandbox_id` (two instances have different IDs), `test_id_before_session` (returns _sandbox_id), `test_id_after_session` (returns session-based ID).

### Implementation for US4+US5

<!-- sequential -->
- [x] T011 [US4][US5] Implement `from_env()` classmethod in src/deepagents_contrib_aws/agentcore_sandbox.py: accept `**kwargs` (`region_name`, `session_timeout_seconds`, `code_interpreter_identifier` — all `| None`). Resolve region: kwarg > `AGENTCORE_REGION` > `AWS_REGION` > `AWS_DEFAULT_REGION` > `"us-west-2"`. Resolve timeout: kwarg > `AGENTCORE_SESSION_TIMEOUT` > `900`. Validate timeout is int and <= 28800, raise `ValueError` if not. Resolve identifier: kwarg > `AGENTCORE_CODE_INTERPRETER_ID` > `"aws.codeinterpreter.v1"`. Return `cls(region_name=region, session_timeout_seconds=timeout, ...)`.

**Checkpoint**: from_env() works with all env var combinations, lifecycle fully tested — all test_lifecycle.py tests pass

---

## Phase 6: User Story 6 — Optional Dependency & Package Integration (Priority: P3)

**Goal**: Wire up `AgentCoreCodeInterpreterSandbox` as a lazy import in `__init__.py` so S3Backend users are unaffected when `bedrock-agentcore` is not installed.

**Independent Test**: Import `S3Backend` without bedrock-agentcore installed — works. Import `AgentCoreCodeInterpreterSandbox` without it — raises `ImportError` with install message.

### Implementation for US6

<!-- sequential -->
- [x] T012 [US6] Update src/deepagents_contrib_aws/__init__.py: add lazy import for `AgentCoreCodeInterpreterSandbox` — use `try/except ImportError` to handle missing `bedrock-agentcore`. When imported successfully, add to `__all__`. When not installed, define a stub that raises `ImportError` with message `"bedrock-agentcore is required for AgentCoreCodeInterpreterSandbox. Install with: pip install deepagents-contrib-aws[agentcore]"`. Ensure `S3Backend` import is unaffected.

**Checkpoint**: Package import works with and without bedrock-agentcore installed

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, version bump, integration tests, final validation

<!-- parallel-group: 2 (max 3 concurrent) -->
- [x] T013 [P] Create tests/agentcore_sandbox/test_integration.py with `@pytest.mark.integration` tests: `test_python_execution` (real executeCode), `test_shell_command` (real executeCommand), `test_file_round_trip` (upload + download text and binary), `test_session_lifecycle` (start, execute, stop). Add skip condition: `pytest.mark.skipif(not os.environ.get("AGENTCORE_TEST_REGION"), reason="AGENTCORE_TEST_REGION not set")`. Document prerequisites in module docstring.

- [x] T014 [P] Update README.md: add `## AgentCore Code Interpreter Sandbox` section after S3Backend section. Include: feature description, installation (`pip install deepagents-contrib-aws[agentcore]`), quick start (minimal constructor, explicit constructor, context manager), from_env() with override kwargs table (`region_name` → `AGENTCORE_REGION`/`AWS_REGION`/`AWS_DEFAULT_REGION`, `session_timeout_seconds` → `AGENTCORE_SESSION_TIMEOUT`, `code_interpreter_identifier` → `AGENTCORE_CODE_INTERPRETER_ID`), basic operations (execute Python, execute shell, upload/download files), with deepagents integration example. Follow existing README style and structure.

- [x] T015 [P] Bump version to 0.2.0 in BOTH pyproject.toml (`version = "0.2.0"`) AND src/deepagents_contrib_aws/__init__.py (`__version__ = "0.2.0"`)

<!-- sequential -->
- [x] T016 Run `ruff check src/ tests/` and fix any linting issues. Ensure all code fits within 88-char line length. Run `pytest` to verify all unit tests pass.

**Checkpoint**: All tests pass, documentation complete, package ready

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 (T001 for imports)
- **Phase 3 (US1+US2 Execute)**: Depends on Phase 2 (class skeleton)
- **Phase 4 (US3 Files)**: Depends on Phase 2 (class skeleton + _ensure_session)
- **Phase 5 (US4+US5 Config/Lifecycle)**: Depends on Phase 2 (class skeleton)
- **Phase 6 (US6 Packaging)**: Depends on Phase 2 (class exists to import)
- **Phase 7 (Polish)**: Depends on Phases 3-6 (all features implemented)

### Parallel Opportunities

- **Phase 1**: T002 and T003 can run in parallel (different files)
- **Phases 3, 4, 5, 6**: Test creation tasks (T005, T007, T010) can run in parallel after Phase 2 completes (different test files). However, implementation tasks (T006, T008, T009, T011) all modify agentcore_sandbox.py and MUST run sequentially across phases
- **Phase 7**: T013, T014, T015 can run in parallel (different files)

### Within Each Phase

- Tests before implementation (tests created first, then implementation makes them pass)
- Implementation tasks are sequential within a phase (same source file)

---

## Parallel Example: Phase 1

```bash
# After T001 completes:
Task T002: "Create tests/agentcore_sandbox/__init__.py"
Task T003: "Create tests/agentcore_sandbox/conftest.py"
```

## Parallel Example: Phase 7

```bash
# After all user story phases complete:
Task T013: "Create tests/agentcore_sandbox/test_integration.py"
Task T014: "Update README.md"
Task T015: "Bump version to 0.2.0"
```

---

## Implementation Strategy

### MVP First (User Stories 1+2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (class skeleton)
3. Complete Phase 3: US1+US2 (execute Python + shell)
4. **STOP and VALIDATE**: Run test_execute.py — sandbox can execute code
5. This is a functional MVP — execute() works for agents

### Incremental Delivery

1. Setup + Foundational → Class skeleton ready
2. Add US1+US2 → Execute works → MVP!
3. Add US3 → File operations work
4. Add US4+US5 → from_env() and lifecycle work
5. Add US6 → Optional dependency packaging works
6. Polish → README, version bump, integration tests

---

## Notes

- All implementation tasks modify `src/deepagents_contrib_aws/agentcore_sandbox.py` — they MUST run sequentially
- Test files are independent — test creation tasks could run in parallel, but they depend on conftest (T003)
- US1 and US2 are combined because they share `execute()` in the same file — cannot be parallelized
- Reference implementation at `/home/dhamijag/playground/deep-agents/sdk/hello_world/agentcore_sandbox.py` — use as guidance for `_extract_python_from_command()` and response parsing
- Ruff line-length 88 — break long function calls proactively
- No `[tool.uv.sources]` local paths — all deps from PyPI
