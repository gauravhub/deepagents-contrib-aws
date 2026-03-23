# Feature Specification: AgentCore Code Interpreter Sandbox

**Feature Branch**: `feature/agentcore-sandbox`
**Created**: 2026-03-22
**Status**: Draft
**Input**: User description: "Implement a sandbox backend for the deepagents framework using Amazon Bedrock AgentCore Code Interpreter"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Execute Python Code in Cloud Sandbox (Priority: P1)

A developer using the deepagents framework wants to run Python code in a managed cloud sandbox instead of locally. They create an `AgentCoreCodeInterpreterSandbox`, call `execute()` with a `python3 -c "..."` command, and receive the output. The sandbox session starts lazily on first use and maintains Python variable state across calls within the same session.

**Why this priority**: This is the core value proposition — executing Python in a managed, isolated cloud environment. Without this, the backend has no purpose. It also enables all file operations inherited from `BaseSandbox`, which internally generate `python3 -c` commands.

**Independent Test**: Can be fully tested by creating a sandbox instance, executing a Python command, and verifying the response contains expected output with exit code 0.

**Acceptance Scenarios**:

1. **Given** a sandbox instance with no active session, **When** the developer calls `execute('python3 -c "print(42)"')`, **Then** a session is created lazily and the response contains output `"42"` with exit_code 0 and truncated False.
2. **Given** an active sandbox session, **When** the developer executes `python3 -c "x = 10"` followed by `python3 -c "print(x)"`, **Then** the second call returns `"10"`, demonstrating variable state is preserved across calls.
3. **Given** an active sandbox session, **When** the developer executes Python code that raises an exception, **Then** the response contains the error message with exit_code 1 and no exception is raised to the caller.
4. **Given** an active sandbox session, **When** execution output exceeds the configured `max_output_chars` limit, **Then** the response is truncated with a truncation notice and `truncated=True`.

---

### User Story 2 - Execute Shell Commands in Cloud Sandbox (Priority: P1)

A developer or an AI agent wants to run arbitrary shell commands (not just Python) in the cloud sandbox. They call `execute()` with a regular shell command like `ls -la` or `cat /etc/os-release`, and the sandbox routes it through the AgentCore `executeCommand` API.

**Why this priority**: This removes the key limitation of the reference implementation (Python-only). Supporting shell commands makes the sandbox a general-purpose execution environment, which is essential for agent workflows that need to install packages, run scripts, or inspect the environment.

**Independent Test**: Can be fully tested by creating a sandbox, executing a shell command like `echo hello`, and verifying the response contains the expected output.

**Acceptance Scenarios**:

1. **Given** an active sandbox session, **When** the developer calls `execute("echo hello")`, **Then** the response contains `"hello"` with exit_code 0.
2. **Given** an active sandbox session, **When** the developer calls `execute("ls /nonexistent")`, **Then** the response contains an error message with exit_code 1.
3. **Given** a `python3 -c "..."` command, **When** `execute()` is called, **Then** it is routed to `executeCode` (not `executeCommand`) to preserve Python variable state.

---

### User Story 3 - Upload and Download Files (Priority: P2)

A developer wants to transfer files to and from the cloud sandbox. They use `upload_files()` to send files into the sandbox environment and `download_files()` to retrieve results. The operations use native AgentCore file APIs for efficiency rather than Python-based workarounds.

**Why this priority**: File operations are essential for real-world workflows (uploading data, downloading results) but are secondary to code execution. The inherited `BaseSandbox` file operations (read, write, edit) already work via `execute()`, so this provides a more efficient bulk transfer mechanism.

**Independent Test**: Can be fully tested by uploading a text file and a binary file, then downloading them back and verifying contents match.

**Acceptance Scenarios**:

1. **Given** an active sandbox session, **When** the developer uploads a text file via `upload_files([("/tmp/test.txt", b"hello")])`, **Then** the response indicates success with no error.
2. **Given** an uploaded file in the sandbox, **When** the developer calls `download_files(["/tmp/test.txt"])`, **Then** the response contains the file content as bytes with no error.
3. **Given** a download request for a non-existent file, **When** `download_files(["/tmp/missing.txt"])` is called, **Then** the response contains `error="file_not_found"` and `content=None`.
4. **Given** a batch of files where some succeed and some fail, **When** upload or download is called, **Then** each file gets its own success/error response (partial success).
5. **Given** a binary file (e.g., an image), **When** it is uploaded and downloaded, **Then** the content is preserved exactly (binary-safe round-trip).

---

### User Story 4 - Configure via Environment Variables (Priority: P2)

A developer deploying in AWS (Lambda, ECS, EC2) wants to configure the sandbox without hardcoding values. They use the `from_env()` factory method which reads region, timeout, and identifier from environment variables, falling back to sensible defaults.

**Why this priority**: Environment-based configuration is standard practice for AWS services and enables deployment flexibility. However, direct constructor usage also works, so this is a convenience feature.

**Independent Test**: Can be fully tested by setting environment variables, calling `from_env()`, and verifying the instance is configured correctly.

**Acceptance Scenarios**:

1. **Given** `AGENTCORE_REGION=eu-west-1` is set, **When** `from_env()` is called, **Then** the sandbox uses region `eu-west-1`.
2. **Given** no `AGENTCORE_REGION` but `AWS_REGION=us-east-1` is set, **When** `from_env()` is called, **Then** the sandbox uses region `us-east-1`.
3. **Given** no region environment variables are set, **When** `from_env()` is called, **Then** the sandbox uses the default region `us-west-2`.
4. **Given** `AGENTCORE_SESSION_TIMEOUT=3600` is set, **When** `from_env()` is called, **Then** the sandbox uses a 3600-second timeout.
5. **Given** `from_env()` is called with an explicit keyword argument `region_name="ap-southeast-1"`, **When** `AGENTCORE_REGION` is also set, **Then** the keyword argument takes precedence.

---

### User Story 5 - Manage Sandbox Lifecycle (Priority: P2)

A developer wants predictable resource management for the cloud sandbox session. They can use `stop()` for explicit cleanup, or use the context manager pattern (`with` statement) for automatic cleanup, ensuring AgentCore sessions are released even if exceptions occur.

**Why this priority**: Cloud sandbox sessions consume resources. Proper lifecycle management prevents resource leaks, which matters for long-running applications or batch processing.

**Independent Test**: Can be fully tested by creating a sandbox, executing a command, calling `stop()`, and verifying the session is released. Context manager can be tested by verifying `stop()` is called on exit.

**Acceptance Scenarios**:

1. **Given** a sandbox with an active session, **When** `stop()` is called, **Then** the AgentCore session is terminated and resources are released.
2. **Given** a sandbox used as a context manager (`with AgentCoreCodeInterpreterSandbox() as sb`), **When** the `with` block exits (normally or via exception), **Then** `stop()` is called automatically.
3. **Given** a sandbox that has not been used yet (no session started), **When** `stop()` is called, **Then** nothing happens (no error raised).
4. **Given** a sandbox whose session has timed out, **When** `execute()` is called again, **Then** a new session is created transparently.

---

### User Story 6 - Install as Optional Dependency (Priority: P3)

A developer using `deepagents-contrib-aws` only for S3Backend wants to avoid installing `bedrock-agentcore` and its dependencies. The AgentCore sandbox is available as an optional extra: `pip install deepagents-contrib-aws[agentcore]`.

**Why this priority**: Package hygiene — keeping the base package lightweight. Users who only need S3 should not be forced to install AgentCore SDK dependencies.

**Independent Test**: Can be tested by installing the package without the `[agentcore]` extra and verifying that S3Backend works while importing AgentCoreCodeInterpreterSandbox raises an informative ImportError.

**Acceptance Scenarios**:

1. **Given** the package installed with `pip install deepagents-contrib-aws[agentcore]`, **When** the developer imports `AgentCoreCodeInterpreterSandbox`, **Then** the import succeeds.
2. **Given** the package installed without the agentcore extra, **When** the developer imports `AgentCoreCodeInterpreterSandbox`, **Then** an `ImportError` is raised with a message explaining how to install the required dependency.
3. **Given** the package installed without the agentcore extra, **When** the developer uses `S3Backend`, **Then** it works normally without any errors.

---

### Edge Cases

- What happens when the AgentCore service is unavailable or returns a network error during `execute()`? The error is wrapped in `ExecuteResponse` with exit_code 1 — no exception propagates.
- What happens when a session timeout occurs mid-execution? The sandbox detects the expired session and creates a new one transparently on the next call.
- What happens when `execute()` receives an empty command string? It is passed to `executeCommand` as-is; the resulting error (if any) is returned in `ExecuteResponse`.
- What happens when `upload_files()` receives a file with an invalid path (e.g., path containing null bytes)? The error is returned as `FileUploadResponse` with `error="invalid_path"`.
- What happens when the streaming response from AgentCore contains mixed text and error content? Both are collected; exit_code is set to 1 if any error content is present.
- What happens when `from_env()` receives both an environment variable and an explicit keyword argument? The keyword argument takes precedence over the environment variable.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extend `BaseSandbox` and implement the four abstract members: `execute()`, `id` property, `upload_files()`, and `download_files()`.
- **FR-002**: System MUST support executing Python code extracted from `python3 -c "..."` commands via the AgentCore `executeCode` API, preserving variable state across calls within the same session.
- **FR-003**: System MUST support executing arbitrary shell commands via the AgentCore `executeCommand` API for all commands that are not `python3 -c "..."`.
- **FR-004**: System MUST return all execution results as `ExecuteResponse` objects — never raising exceptions to callers from `execute()`.
- **FR-005**: System MUST truncate execution output exceeding the configured `max_output_chars` limit and set `truncated=True` on the response.
- **FR-006**: System MUST initialize the AgentCore session lazily on the first `execute()` call, not during construction.
- **FR-007**: System MUST provide a `stop()` method that terminates the AgentCore session and releases resources.
- **FR-008**: System MUST support context manager protocol (`__enter__`/`__exit__`) for automatic session cleanup.
- **FR-009**: System MUST upload files using the AgentCore native `writeFiles` API, handling text and binary content appropriately.
- **FR-010**: System MUST download files using the AgentCore native `readFiles` API, handling text and binary content appropriately.
- **FR-011**: System MUST support partial success in file operations — each file in a batch gets its own success/error response.
- **FR-012**: System MUST map file operation errors to standardized `FileOperationError` codes: `file_not_found`, `permission_denied`, `is_directory`, `invalid_path`.
- **FR-013**: System MUST provide a `from_env()` classmethod that reads configuration from environment variables (`AGENTCORE_REGION`, `AWS_REGION`, `AWS_DEFAULT_REGION`, `AGENTCORE_SESSION_TIMEOUT`, `AGENTCORE_CODE_INTERPRETER_ID`), with keyword argument overrides.
- **FR-014**: System MUST generate a unique sandbox ID per instance.
- **FR-015**: System MUST handle session timeout gracefully by creating a new session transparently when the previous one has expired.
- **FR-016**: System MUST be installable as an optional dependency via `pip install deepagents-contrib-aws[agentcore]` without affecting existing S3Backend users.
- **FR-017**: System MUST accept constructor parameters: `region_name` (default `"us-west-2"`), `session_timeout_seconds` (default 900, max 28800), `max_output_chars` (default 100,000), and optional `code_interpreter_identifier`.
- **FR-018**: The `from_env()` method MAY raise `ValueError` for invalid configuration values (e.g., timeout exceeding maximum).

### Key Entities

- **AgentCoreCodeInterpreterSandbox**: The main class extending `BaseSandbox`. Wraps an AgentCore Code Interpreter session and delegates execution to the cloud service.
- **CodeInterpreter Session**: A remote execution environment managed by the AgentCore service. Created lazily, identified by session ID, with configurable timeout.
- **ExecuteResponse**: Standardized result of command execution containing output text, exit code, and truncation flag.
- **FileUploadResponse / FileDownloadResponse**: Per-file result objects for batch file operations, with standardized error codes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can execute Python code and receive results within the sandbox, with variable state preserved across consecutive calls in the same session.
- **SC-002**: Developers can execute arbitrary shell commands (not just Python) in the sandbox, removing the Python-only limitation of the reference implementation.
- **SC-003**: All unit tests pass with mocked AgentCore client — covering execution, file operations, lifecycle management, and configuration.
- **SC-004**: File upload and download operations handle both text and binary content correctly with binary-safe round-trips.
- **SC-005**: The sandbox can be installed as an optional extra without impacting existing S3Backend users — installing without `[agentcore]` extra does not pull in `bedrock-agentcore` dependencies.
- **SC-006**: The `from_env()` factory correctly resolves configuration from environment variables with the documented precedence order.
- **SC-007**: No exceptions propagate from `execute()` to callers — all errors are wrapped in `ExecuteResponse`.
- **SC-008**: Session lifecycle is managed correctly: lazy initialization, explicit `stop()`, and context manager cleanup all work as expected.

## Clarifications

### Session 2026-03-22

- No critical ambiguities detected. Spec is comprehensive as written.
- Deferred to planning: observability/logging, thread safety, session timeout detection mechanism (all low-impact implementation details).

## Assumptions

- The `bedrock-agentcore` Python SDK is available on PyPI and provides the `CodeInterpreter` client with `start()`, `invoke()`, and `stop()` methods.
- The AgentCore `executeCommand` API accepts shell commands and returns streaming responses in the same format as `executeCode`.
- The AgentCore `writeFiles` and `readFiles` APIs accept the documented request format with `"text"` and `"blob"` fields.
- AWS credentials are handled by the standard boto3 credential chain — the sandbox does not manage credentials directly.
- The `deepagents>=0.4.0` package on PyPI exports `BaseSandbox`, `ExecuteResponse`, `FileUploadResponse`, `FileDownloadResponse`, and `FileOperationError`.
- Session timeout is handled server-side by AgentCore; the sandbox detects timeout errors in response and re-creates the session.
