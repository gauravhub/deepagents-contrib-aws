# Data Model: AgentCore Code Interpreter Sandbox

**Date**: 2026-03-22

## Entities

### AgentCoreCodeInterpreterSandbox

The main class. Extends `BaseSandbox` (which implements `SandboxBackendProtocol`).

**Attributes**:

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `_region` | `str` | `"us-west-2"` | AWS region for AgentCore |
| `_session_timeout` | `int` | `900` | Session timeout in seconds (max 28800) |
| `_max_output_chars` | `int` | `100_000` | Output truncation threshold |
| `_code_interpreter_id` | `str` | `"aws.codeinterpreter.v1"` | Interpreter identifier |
| `_client` | `CodeInterpreter \| None` | `None` | SDK client (lazy) |
| `_session_id` | `str \| None` | `None` | Active session ID |
| `_sandbox_id` | `str` | auto-generated | Unique instance ID (`agentcore-ci-{uuid8}`) |

**State transitions**:

```
CREATED → ACTIVE → STOPPED
  │                   │
  │                   ▼
  └──────────────  CREATED (session timeout → re-create on next execute)
```

- `CREATED`: Constructor called, no session yet (`_client is None`)
- `ACTIVE`: First `execute()` called, session started (`_client` and `_session_id` set)
- `STOPPED`: `stop()` called, client released (`_client = None`, `_session_id = None`)

### Upstream Protocol Types (from deepagents)

These are NOT defined by this feature — they're imported from `deepagents.backends.protocol`:

- **ExecuteResponse**: `output: str`, `exit_code: int | None`, `truncated: bool`
- **FileUploadResponse**: `path: str`, `error: FileOperationError | None`
- **FileDownloadResponse**: `path: str`, `content: bytes | None`, `error: FileOperationError | None`
- **FileOperationError**: `Literal["file_not_found", "permission_denied", "is_directory", "invalid_path"]`

## Relationships

```
AgentCoreCodeInterpreterSandbox
  ├── extends: BaseSandbox (deepagents.backends.sandbox)
  │     └── implements: SandboxBackendProtocol
  ├── uses: CodeInterpreter (bedrock_agentcore.tools)
  │     └── manages: AgentCore session (remote)
  └── returns: ExecuteResponse, FileUploadResponse, FileDownloadResponse
```

## Key Design Decisions

1. **Lazy session**: Session not created until first `execute()`, keeping construction cheap and side-effect-free.
2. **Path normalization**: `writeFiles` requires relative paths — strip leading `/` from paths passed by callers.
3. **Binary detection**: For `upload_files`, attempt UTF-8 decode to determine text vs binary; use `blob` (base64) for binary.
4. **No thread safety**: Single-threaded usage assumed (consistent with upstream `CodeInterpreter` SDK).
