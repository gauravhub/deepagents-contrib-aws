# AgentCore Code Interpreter Sandbox

A `SandboxBackendProtocol` implementation that executes code and commands via [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/) Code Interpreter. Supports Python execution (with variable state preserved across calls) and arbitrary shell commands. File operations use native AgentCore APIs for efficient transfers.

## Installation

```bash
pip install deepagents-contrib-aws[agentcore]
```

The `[agentcore]` extra installs the `bedrock-agentcore` SDK. If you only need `S3Backend`, install without the extra — the sandbox won't be available but nothing else is affected.

## Quick Start

### From constructor

**Minimal** — session starts lazily on first `execute()` call:

```python
from deepagents_contrib_aws import AgentCoreCodeInterpreterSandbox

sandbox = AgentCoreCodeInterpreterSandbox(region_name="us-west-2")

# Execute Python (variable state preserved across calls)
result = sandbox.execute('python3 -c "x = 42; print(x)"')
print(result.output)  # "42"

# Execute shell commands
result = sandbox.execute("echo hello && ls /tmp")
print(result.output)

sandbox.stop()
```

**With context manager** — session automatically cleaned up on exit:

```python
from deepagents_contrib_aws import AgentCoreCodeInterpreterSandbox

with AgentCoreCodeInterpreterSandbox() as sandbox:
    result = sandbox.execute('python3 -c "print(1 + 1)"')
    print(result.output)  # "2"
```

### From environment variables

```bash
export AGENTCORE_REGION=us-west-2          # or AWS_REGION / AWS_DEFAULT_REGION
export AGENTCORE_SESSION_TIMEOUT=1800      # optional (default: 900)
```

```python
from deepagents_contrib_aws import AgentCoreCodeInterpreterSandbox

sandbox = AgentCoreCodeInterpreterSandbox.from_env()
```

**Override** — `from_env()` accepts keyword arguments that take precedence over environment variables:

| Kwarg | Overrides env var |
|-------|-------------------|
| `region_name` | `AGENTCORE_REGION` / `AWS_REGION` / `AWS_DEFAULT_REGION` |
| `session_timeout_seconds` | `AGENTCORE_SESSION_TIMEOUT` |
| `code_interpreter_identifier` | `AGENTCORE_CODE_INTERPRETER_ID` |

### With deepagents

```python
from deepagents import create_deep_agent
from deepagents_contrib_aws import AgentCoreCodeInterpreterSandbox

sandbox = AgentCoreCodeInterpreterSandbox.from_env()
agent = create_deep_agent(backend=sandbox)
```

## Command Execution

The sandbox routes commands based on their format:

- **`python3 -c "..."`** commands are sent to `executeCode`, which preserves Python variable state across consecutive calls within the same session.
- **All other commands** are sent to `executeCommand` for shell execution.

```python
with AgentCoreCodeInterpreterSandbox() as sandbox:
    # Python — state preserved across calls
    sandbox.execute('python3 -c "x = 10"')
    result = sandbox.execute('python3 -c "print(x * 2)"')
    print(result.output)  # "20"

    # Shell — arbitrary commands
    result = sandbox.execute("pip install pandas && python3 -c \"import pandas; print(pandas.__version__)\"")
    print(result.output)
```

Errors are never raised from `execute()` — they are wrapped in the response:

```python
result = sandbox.execute('python3 -c "1/0"')
print(result.exit_code)  # 1
print(result.output)     # "ZeroDivisionError: division by zero"
```

## File Operations

Upload and download files using native AgentCore APIs. Text and binary content are handled automatically.

```python
with AgentCoreCodeInterpreterSandbox() as sandbox:
    # Upload files (text and binary)
    upload_results = sandbox.upload_files([
        ("/tmp/data.csv", b"name,value\nfoo,42"),
        ("/tmp/image.png", open("local.png", "rb").read()),
    ])

    # Download files
    download_results = sandbox.download_files(["/tmp/data.csv"])
    print(download_results[0].content)  # b"name,value\nfoo,42"
```

Batch operations support partial success — each file gets its own response with success or error status:

```python
results = sandbox.download_files(["/tmp/exists.txt", "/tmp/missing.txt"])
# results[0].content = b"..."    results[0].error = None
# results[1].content = None      results[1].error = "file_not_found"
```

## Session Lifecycle

- **Lazy initialization**: The AgentCore session starts on the first `execute()` call, not during construction.
- **Explicit cleanup**: Call `stop()` to terminate the session and release resources.
- **Context manager**: Use `with` for automatic cleanup, even if exceptions occur.
- **Timeout recovery**: If a session times out, the sandbox transparently creates a new one on the next call.

## Configuration Reference

### Constructor parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `region_name` | `str` | `"us-west-2"` | AWS region for AgentCore |
| `session_timeout_seconds` | `int` | `900` | Session timeout in seconds (max 28800) |
| `max_output_chars` | `int` | `100_000` | Truncate output above this limit |
| `code_interpreter_identifier` | `str` | `"aws.codeinterpreter.v1"` | Interpreter ID |

### Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AGENTCORE_REGION` | No | `"us-west-2"` | AWS region (checked first) |
| `AWS_REGION` | No | -- | AWS region (fallback; auto-set by Lambda) |
| `AWS_DEFAULT_REGION` | No | -- | AWS region (standard boto3 fallback) |
| `AGENTCORE_SESSION_TIMEOUT` | No | `900` | Session timeout in seconds |
| `AGENTCORE_CODE_INTERPRETER_ID` | No | `"aws.codeinterpreter.v1"` | Interpreter ID |

### AWS Credentials

Credentials are resolved via the standard boto3 credential chain:

1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`)
2. Shared credentials file (`~/.aws/credentials`)
3. AWS SSO (`aws sso login`)
4. IAM role (EC2, ECS, Lambda)

### Required IAM Permissions

The calling identity needs permissions for bedrock-agentcore Code Interpreter operations. Refer to the [bedrock-agentcore documentation](https://github.com/aws/bedrock-agentcore-sdk-python) for the specific IAM actions required.
