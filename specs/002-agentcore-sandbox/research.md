# Research: AgentCore Code Interpreter Sandbox

**Date**: 2026-03-22

## R1: bedrock-agentcore SDK API Surface

**Decision**: Use `CodeInterpreter` from `bedrock_agentcore.tools.code_interpreter_client` with `invoke()` for low-level control, not the convenience wrappers.

**Rationale**: The `invoke()` method provides direct access to `executeCode`, `executeCommand`, `writeFiles`, `readFiles` — exactly matching the spec requirements. The convenience methods (`execute_code`, `execute_command`, `download_file`) add extra validation (e.g., rejecting absolute paths) that may conflict with `BaseSandbox` behavior.

**Key findings**:
- `CodeInterpreter(region, session=None, integration_source=None)` — constructor
- `start(identifier=None, name=None, session_timeout_seconds=None)` → returns `str` (session_id)
- `invoke(method, params=None)` → returns `dict` (NOT streaming — the "stream" key is a list in the response dict)
- `stop()` → returns `bool`
- Auto-start: `invoke()` automatically calls `start()` if no session is active — BUT we need explicit control for timeout/identifier params, so we should manage sessions ourselves
- Paths: `writeFiles` uses relative paths; `upload_file()` convenience method rejects absolute paths with ValueError

**Alternatives considered**:
- Convenience wrappers (`execute_code`, `upload_files`): Rejected — `upload_file` rejects absolute paths, but `BaseSandbox` may pass absolute paths from file operations
- Raw boto3 calls: Rejected — the SDK handles session management, endpoint configuration, and telemetry

## R2: Response Format for executeCode/executeCommand

**Decision**: Parse the `stream` key from `invoke()` response dict to extract text output and errors.

**Rationale**: Both `executeCode` and `executeCommand` return responses with a `stream` key containing a list of event dicts. Each event has a `result.content[]` list with items of type `text` or `error`.

**Response structure** (from reference implementation and SDK source):
```python
{
    "stream": [
        {
            "result": {
                "content": [
                    {"type": "text", "text": "output text"},
                    {"type": "error", "text": "error message"}
                ]
            }
        }
    ]
}
```

**Key findings**:
- `type: "text"` → stdout/normal output
- `type: "error"` → error output; set exit_code=1
- Multiple events may exist in the stream list
- The reference implementation joins output parts with `\n`

## R3: File Upload/Download via Native API

**Decision**: Use `invoke("writeFiles", ...)` and `invoke("readFiles", ...)` directly instead of Python-snippet workarounds.

**Rationale**: The native APIs handle text/binary content natively and are more efficient than encoding files as Python code strings. The spec explicitly requires native API usage.

**writeFiles format**:
```python
{"content": [{"path": "relative/path", "text": "content"}]}  # text
{"content": [{"path": "relative/path", "blob": "base64..."}]}  # binary
```

**readFiles response** (via `stream` key):
```python
{
    "stream": [
        {
            "result": {
                "content": [
                    {
                        "type": "resource",
                        "resource": {
                            "uri": "file://path",
                            "text": "content"  # or "blob": "base64..."
                        }
                    }
                ]
            }
        }
    ]
}
```

**Key findings**:
- Paths must be relative (not absolute) for writeFiles — need to strip leading `/` from paths passed by `BaseSandbox`
- Binary content uses `blob` field with base64 encoding
- readFiles response uses `resource.text` for text files and `resource.blob` for binary files

## R4: Session Timeout Detection

**Decision**: Catch exceptions from `invoke()` that indicate session expiry, then re-create the session and retry.

**Rationale**: AgentCore sessions have server-side timeouts. When a session expires, `invoke()` raises a `botocore.exceptions.ClientError` or similar exception. The sandbox should catch this, call `stop()` + `start()`, and retry the operation once.

**Key findings**:
- No explicit "session expired" error code documented in SDK
- Best approach: catch any exception from `invoke()`, attempt session re-creation once, retry the operation
- If retry also fails, return the error in `ExecuteResponse`

## R5: Optional Dependency Pattern

**Decision**: Use `try/except ImportError` for `bedrock-agentcore` import, matching the S3Backend pattern for boto3.

**Rationale**: Consistent with existing codebase pattern. The `[agentcore]` extra in pyproject.toml makes installation explicit.

**pyproject.toml changes**:
```toml
[project.optional-dependencies]
agentcore = ["bedrock-agentcore"]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff>=0.4",
    "moto[s3]>=5.0",
    "bedrock-agentcore",  # for sandbox tests
]
```

## R6: Python Command Extraction

**Decision**: Reuse the `_extract_python_from_command()` helper from the reference implementation.

**Rationale**: The regex-based extraction handles `python3 -c "..."` and `python3 -c '...'` with proper quote escaping. It's well-tested in the reference and matches `BaseSandbox`'s internal command generation.

**Key findings**:
- `BaseSandbox` generates commands like `python3 -c "import os; ..."` for file operations
- The extraction must handle backslash-escaped quotes within the command
- Non-matching commands fall through to `executeCommand` (shell execution)
