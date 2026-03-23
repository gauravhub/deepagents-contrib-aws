# Public API Contract: AgentCoreCodeInterpreterSandbox

**Date**: 2026-03-22

## Class: AgentCoreCodeInterpreterSandbox

```python
from deepagents_contrib_aws import AgentCoreCodeInterpreterSandbox
```

### Constructor

```python
AgentCoreCodeInterpreterSandbox(
    region_name: str = "us-west-2",
    session_timeout_seconds: int = 900,
    max_output_chars: int = 100_000,
    code_interpreter_identifier: str = "aws.codeinterpreter.v1",
)
```

### Factory

```python
@classmethod
def from_env(
    cls,
    *,
    region_name: str | None = None,
    session_timeout_seconds: int | None = None,
    code_interpreter_identifier: str | None = None,
) -> AgentCoreCodeInterpreterSandbox
```

**Environment variable precedence**:
- Region: kwarg > `AGENTCORE_REGION` > `AWS_REGION` > `AWS_DEFAULT_REGION` > `"us-west-2"`
- Timeout: kwarg > `AGENTCORE_SESSION_TIMEOUT` > `900`
- Identifier: kwarg > `AGENTCORE_CODE_INTERPRETER_ID` > `"aws.codeinterpreter.v1"`

**Raises**: `ValueError` if timeout is invalid (non-integer or exceeds 28800).

### Protocol Methods (from BaseSandbox)

```python
def execute(self, command: str) -> ExecuteResponse
```
- `python3 -c "..."` → routed to `executeCode` (preserves Python state)
- All other commands → routed to `executeCommand` (shell execution)
- Never raises — errors wrapped in `ExecuteResponse(exit_code=1)`

```python
@property
def id(self) -> str
```
- Returns unique sandbox identifier

```python
def upload_files(
    self, files: list[tuple[str, bytes]]
) -> list[FileUploadResponse]
```
- Uses native `writeFiles` API
- Text vs binary auto-detected; binary uses base64

```python
def download_files(
    self, paths: list[str]
) -> list[FileDownloadResponse]
```
- Uses native `readFiles` API
- Returns bytes for both text and binary files

### Lifecycle Methods

```python
def stop(self) -> None
```
- Terminates the AgentCore session
- Safe to call multiple times or before any session started

```python
def __enter__(self) -> AgentCoreCodeInterpreterSandbox
def __exit__(self, *args) -> None
```
- Context manager support; calls `stop()` on exit

### Package Extras

```bash
pip install deepagents-contrib-aws[agentcore]
```

Import without the extra installed raises `ImportError` with installation instructions.
