# AgentCore Code Interpreter Sandbox Feature Prompt

## Feature Description

Implement a sandbox backend for the [deepagents](https://github.com/langchain-ai/deepagents) framework by extending `BaseSandbox` (which implements `SandboxBackendProtocol`) to use Amazon Bedrock AgentCore Code Interpreter as the execution environment. This backend will be added to the existing `deepagents-contrib-aws` PyPI package.

## Context

The deepagents framework defines a `SandboxBackendProtocol` (extending `BackendProtocol`) that adds shell command execution via an `execute()` method. `BaseSandbox` is an abstract class that implements all file operations (`ls`, `read`, `write`, `edit`, `grep`, `glob`) using shell commands delegated to `execute()`. Subclasses only need to implement `execute()`, `id`, `upload_files()`, and `download_files()`.

Existing partner sandbox implementations follow this pattern:
- **ModalSandbox** (`langchain-modal`): wraps `modal.Sandbox`, delegates `execute()` to `sandbox.exec("bash", "-c", command)`
- **DaytonaSandbox** (`langchain-daytona`): wraps `daytona.Sandbox`, uses async session API with polling
- **RunloopSandbox** (`langchain-runloop`): wraps Runloop `Devbox`, delegates to `devbox.cmd.exec()`

All partners accept a pre-created SDK object, implement the 4 abstract methods, and set a 30-minute default timeout.

**Upstream protocol**: `deepagents.backends.protocol.SandboxBackendProtocol` and `deepagents.backends.sandbox.BaseSandbox` (available in deepagents>=0.4.0 on PyPI). Subclasses only need to implement `execute()`, `id`, `upload_files()`, and `download_files()`.

**Upstream protocol**: `deepagents.backends.protocol.SandboxBackendProtocol` and `deepagents.backends.sandbox.BaseSandbox` (available in deepagents>=0.4.0 on PyPI).

**AgentCore Code Interpreter API**: Uses the `bedrock-agentcore` Python SDK. Key operations:
- `CodeInterpreter(region).start()` — creates a session
- `client.invoke("executeCode", {"language": "python", "code": ...})` — runs Python code
- `client.invoke("executeCommand", {"command": ...})` — runs shell commands
- `client.invoke("writeFiles", {"content": [{"path": ..., "text"|"blob": ...}]})` — uploads files
- `client.invoke("readFiles", {"paths": [...]})` — downloads files
- `client.stop()` — terminates the session

## Learnings from S3Backend Implementation

These lessons from the S3Backend feature MUST be applied:

1. **Strictly use deepagents>=0.4.0 from PyPI** — the latest released version is 0.4.12. Do NOT depend on unreleased versions (0.5.0+). Check https://github.com/langchain-ai/deepagents/releases for the latest release. Verify all imports (`SandboxBackendProtocol`, `BaseSandbox`, `ExecuteResponse`) exist in the installed PyPI version before writing code.

2. **No local source dependencies** — never add `[tool.uv.sources]` with local paths in `pyproject.toml`. All dependencies must resolve from PyPI.

3. **v0.4.x API method names** — the installed version uses `ls_info`, `grep_raw`, `glob_info` (not `ls`, `grep`, `glob`). For this feature, `BaseSandbox` handles file ops internally so this is less relevant, but be aware.

4. **AWS env var conventions**:
   - `AWS_SECURITY_TOKEN` is **legacy** — only use `AWS_SESSION_TOKEN` in test fixtures
   - `AWS_REGION` is checked first (auto-set by Lambda), `AWS_DEFAULT_REGION` as fallback
   - Test conftest should set: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_DEFAULT_REGION` (4 vars, NOT 5)

5. **Test organization** — all tests for this backend go in `tests/agentcore_sandbox/` subfolder (matching `tests/s3_backend/` convention for future backends)

6. **Integration tests** — mark with `@pytest.mark.integration`, skipped by default via `addopts = "-m 'not integration'"` (already configured in pyproject.toml). Document prerequisites clearly.

7. **Ruff line length 88** — format all code to fit within 88 chars. Break long function calls across multiple lines proactively.

8. **README updates** — show both minimal and explicit constructor variants. Document `from_env()` with all override kwargs and their corresponding env vars. Explain where AWS credentials come from.

9. **Version bumping** — update version in BOTH `pyproject.toml` AND `src/deepagents_contrib_aws/__init__.py`.

10. **No exceptions to callers from protocol methods** — `execute()` wraps all errors in `ExecuteResponse`. `from_env()` MAY raise `ValueError` (constructor-time validation, not a protocol method).

## Requirements

### Core
- Extend `BaseSandbox` from `deepagents.backends.sandbox`
- Implement 4 abstract methods: `execute()`, `id` property, `upload_files()`, `download_files()`
- Use the `bedrock-agentcore` Python SDK (`CodeInterpreter` client) for all operations
- Lazy session initialization — session starts on first `execute()` call
- Support both Python code execution AND shell commands via `executeCommand`
- Provide a `stop()` method for explicit session cleanup

### Constructor & Configuration
- Constructor accepts: `region_name: str` (default `"us-west-2"`), `session_timeout_seconds: int` (default 900, max 28800), `max_output_chars: int` (default 100,000), optional `code_interpreter_identifier: str` (default `"aws.codeinterpreter.v1"`)
- `from_env()` classmethod reading from environment variables:
  - `AGENTCORE_REGION` or `AWS_REGION` or `AWS_DEFAULT_REGION` (checked in this order)
  - `AGENTCORE_SESSION_TIMEOUT` (optional, default 900)
  - `AGENTCORE_CODE_INTERPRETER_ID` (optional, default `"aws.codeinterpreter.v1"`)
- AWS credentials via standard boto3 chain (env vars, ~/.aws/credentials, IAM role)

### execute() Implementation
- Extract Python from `python3 -c "..."` commands and run via `executeCode` (preserves variable state across calls)
- For all other commands, run via `executeCommand` (shell execution)
- Parse streaming response to extract text output and errors
- Set `exit_code=0` on success, `exit_code=1` on error
- Truncate output at `max_output_chars` with truncation notice
- Return `ExecuteResponse(output=..., exit_code=..., truncated=...)`
- Never raise exceptions — return error in `ExecuteResponse.output`

### upload_files() / download_files() Implementation
- Use AgentCore's native `writeFiles` / `readFiles` invoke methods (NOT Python snippets like the reference)
- Handle text files via `"text"` field, binary files via `"blob"` field (base64)
- Map errors to `FileOperationError` codes (`file_not_found`, `permission_denied`, `invalid_path`)
- Support partial success — per-file error handling

### Session Lifecycle
- Lazy initialization: session starts on first `execute()` call
- `stop()` method for explicit cleanup
- Context manager support (`__enter__`/`__exit__`) for automatic cleanup
- Generate unique sandbox ID per instance

### Package Structure
```
src/deepagents_contrib_aws/
├── __init__.py                    # Re-export AgentCoreCodeInterpreterSandbox
├── s3_backend.py                  # Existing S3Backend
├── agentcore_sandbox.py           # AgentCoreCodeInterpreterSandbox class
└── py.typed

tests/s3_backend/                  # Existing S3 tests
tests/agentcore_sandbox/
├── __init__.py
├── conftest.py                    # Fixtures with mocked CodeInterpreter
├── test_execute.py                # Tests for execute() — Python and shell commands
├── test_files.py                  # Tests for upload_files/download_files
├── test_lifecycle.py              # Tests for session lifecycle, from_env, context manager
└── test_integration.py            # Integration tests (requires AWS credentials + bedrock-agentcore access)
```

### Testing
- Unit tests with mocked `CodeInterpreter` client (mock `invoke()`, `start()`, `stop()`)
- Test Python extraction from `python3 -c "..."` commands
- Test shell command passthrough via `executeCommand`
- Test streaming response parsing (text, error, mixed)
- Test file upload/download with text and binary content
- Test lazy session init, stop(), context manager
- Test `from_env()` factory
- Integration tests marked with `@pytest.mark.integration` (skipped by default)
- Test conftest sets only: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_DEFAULT_REGION` (no legacy `AWS_SECURITY_TOKEN`)

### Dependencies
- Add `bedrock-agentcore` as an **optional** dependency (extras): `pip install deepagents-contrib-aws[agentcore]`
- Do NOT make it a hard dependency — users who only need S3Backend shouldn't need it
- Add `bedrock-agentcore` as a dev dependency for testing
- `deepagents>=0.4.0` already exists as a dependency — do NOT change the version constraint
- No `[tool.uv.sources]` local paths — all dependencies from PyPI

### Error Handling
- Never raise exceptions from `execute()` — wrap in `ExecuteResponse(output=error_msg, exit_code=1)`
- `from_env()` MAY raise `ValueError` for missing required config (constructor-time, not protocol method)
- Map SDK exceptions to protocol error codes in upload/download
- Handle session timeout gracefully (re-create session if expired)

### Quality
- Type hints on all public methods
- Docstrings on the class and public methods
- Ruff-clean code (line length 88)
- Compatible with deepagents>=0.4.0 (PyPI release — verify imports against installed version)
- Update README.md with AgentCore sandbox usage docs (minimal + explicit constructor, from_env with all kwargs)
