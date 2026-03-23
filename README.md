# deepagents-contrib-aws

AWS backend implementations for the [deepagents](https://github.com/langchain-ai/deepagents) framework.

## Installation

```bash
pip install deepagents-contrib-aws
```

This installs both backends (S3Backend and AgentCoreCodeInterpreterSandbox) and all dependencies.

## Backends

| Backend | Protocol | Description | Docs |
|---------|----------|-------------|------|
| **S3Backend** | `BackendProtocol` | Persists agent workspace files in Amazon S3. Supports `ls`, `read`, `write`, `edit`, `grep`, `glob`, `upload_files`, `download_files`. | [docs/s3-backend.md](docs/s3-backend.md) |
| **AgentCoreCodeInterpreterSandbox** | `SandboxBackendProtocol` | Executes Python and shell commands in a managed cloud sandbox via Amazon Bedrock AgentCore Code Interpreter. Native file upload/download. | [docs/agentcore-sandbox.md](docs/agentcore-sandbox.md) |

## Quick Examples

### S3Backend

```python
from deepagents_contrib_aws import S3Backend

backend = S3Backend(bucket="my-bucket", prefix="agent/workspace/")
backend.write("/hello.py", "print('hello')")
content = backend.read("/hello.py")
```

Or configure from environment variables:

```bash
export S3_BACKEND_BUCKET=my-bucket
```

```python
backend = S3Backend.from_env()
```

See [docs/s3-backend.md](docs/s3-backend.md) for full usage, configuration reference, and all operations.

### AgentCore Code Interpreter Sandbox

```python
from deepagents_contrib_aws import AgentCoreCodeInterpreterSandbox

with AgentCoreCodeInterpreterSandbox(region_name="us-west-2") as sandbox:
    # Python execution (variable state preserved across calls)
    sandbox.execute('python3 -c "x = 42"')
    result = sandbox.execute('python3 -c "print(x)"')
    print(result.output)  # "42"

    # Shell commands
    result = sandbox.execute("echo hello")
    print(result.output)  # "hello"
```

Or configure from environment variables:

```bash
export AGENTCORE_REGION=us-west-2
```

```python
sandbox = AgentCoreCodeInterpreterSandbox.from_env()
```

See [docs/agentcore-sandbox.md](docs/agentcore-sandbox.md) for full usage, file operations, session lifecycle, and configuration reference.

### With deepagents

```python
from deepagents import create_deep_agent
from deepagents_contrib_aws import S3Backend, AgentCoreCodeInterpreterSandbox

# File storage backend
backend = S3Backend.from_env()
agent = create_deep_agent(backend=backend)

# Code execution sandbox
sandbox = AgentCoreCodeInterpreterSandbox.from_env()
agent = create_deep_agent(backend=sandbox)
```

## AWS Credentials

Both backends resolve credentials via the standard boto3 credential chain:

1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`)
2. Shared credentials file (`~/.aws/credentials`)
3. AWS SSO (`aws sso login`)
4. IAM role (EC2, ECS, Lambda)

## Development

See [docs/development.md](docs/development.md) for setup, testing, linting, building, and contributing guidelines.

```bash
# Quick start
uv sync              # install dependencies
uv run pytest        # run unit tests (102 tests, no AWS credentials needed)
uv run ruff check .  # lint
uv build             # build package
```

## License

MIT
