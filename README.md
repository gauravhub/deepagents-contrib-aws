# deepagents-contrib-aws

AWS backend implementations for the [deepagents](https://github.com/langchain-ai/deepagents) framework.

## Backends

### S3Backend

An S3-backed implementation of the `BackendProtocol` that persists agent workspace files in Amazon S3. Supports all eight protocol methods: `ls`, `read`, `write`, `edit`, `grep`, `glob`, `upload_files`, `download_files`.

### AgentCore Code Interpreter Sandbox

A `SandboxBackendProtocol` implementation that executes code and commands via Amazon Bedrock AgentCore Code Interpreter. Supports Python execution (with variable state preserved across calls) and arbitrary shell commands. File operations use native AgentCore APIs for efficient transfers.

## Installation

```bash
# S3Backend only
pip install deepagents-contrib-aws

# With AgentCore sandbox support
pip install deepagents-contrib-aws[agentcore]
```

## Quick Start

### From constructor

**Minimal** — S3 client is created implicitly; region and credentials are picked up from environment variables or `~/.aws/config`:

```python
from deepagents_contrib_aws import S3Backend

backend = S3Backend(bucket="my-bucket", prefix="agent/workspace/")
```

**Explicit** — pass a pre-configured boto3 client (useful for custom endpoints like LocalStack, S3-compatible storage, or reusing an existing session):

```python
import boto3
from deepagents_contrib_aws import S3Backend

client = boto3.client("s3", region_name="us-west-2")
backend = S3Backend(
    bucket="my-bucket",
    prefix="agent/workspace/",
    client=client,
)
```

### From environment variables

**Minimal** — set the bucket and let boto3 resolve credentials and region from `~/.aws/credentials`, `~/.aws/config`, IAM role, or AWS SSO:

```bash
export S3_BACKEND_BUCKET=my-bucket
```

```python
from deepagents_contrib_aws import S3Backend

backend = S3Backend.from_env()
```

**Full** — set all variables explicitly (e.g., in CI/CD, Docker, or Lambda):

```bash
# S3Backend config
export S3_BACKEND_BUCKET=my-bucket
export S3_BACKEND_PREFIX=agent/workspace/
export AWS_REGION=us-west-2  # or AWS_DEFAULT_REGION

# AWS credentials (if not using IAM role or ~/.aws/credentials)
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...  # only for temporary credentials (STS)
```

```python
from deepagents_contrib_aws import S3Backend

backend = S3Backend.from_env()
```

**Override** — `from_env()` accepts keyword arguments that take precedence over environment variables:

| Kwarg | Overrides env var |
|-------|-------------------|
| `bucket` | `S3_BACKEND_BUCKET` |
| `prefix` | `S3_BACKEND_PREFIX` |
| `region_name` | `AWS_REGION` / `AWS_DEFAULT_REGION` |

```python
from deepagents_contrib_aws import S3Backend

# Use env vars but override specific settings
backend = S3Backend.from_env(
    bucket="other-bucket",
    prefix="custom/prefix/",
    region_name="eu-west-1",
)
```

### With deepagents

```python
from deepagents import create_deep_agent
from deepagents_contrib_aws import S3Backend

backend = S3Backend.from_env()
agent = create_deep_agent(backend=backend)
```

### Basic operations

```python
backend = S3Backend(bucket="my-bucket", prefix="demo/")

# Write a file (errors if file already exists)
result = backend.write("/hello.py", "print('hello')")

# Read it back (with line-based pagination)
result = backend.read("/hello.py")

# Edit it (exact string replacement)
result = backend.edit("/hello.py", "hello", "world")

# List directory
result = backend.ls("/")

# Search file contents (literal text, not regex)
result = backend.grep("world", path="/")

# Find files by pattern
result = backend.glob("*.py")

# Bulk upload
result = backend.upload_files([("/a.txt", b"content a"), ("/b.txt", b"content b")])

# Bulk download
result = backend.download_files(["/a.txt", "/b.txt"])
```

## AgentCore Code Interpreter Sandbox

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

**With context manager** — session automatically cleaned up:

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

### File operations

```python
with AgentCoreCodeInterpreterSandbox() as sandbox:
    # Upload files (text and binary)
    sandbox.upload_files([
        ("/tmp/data.csv", b"name,value\nfoo,42"),
        ("/tmp/image.png", open("local.png", "rb").read()),
    ])

    # Download files
    results = sandbox.download_files(["/tmp/data.csv"])
    print(results[0].content)  # b"name,value\nfoo,42"
```

### With deepagents

```python
from deepagents import create_deep_agent
from deepagents_contrib_aws import AgentCoreCodeInterpreterSandbox

sandbox = AgentCoreCodeInterpreterSandbox.from_env()
agent = create_deep_agent(backend=sandbox)
```

### Constructor parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `region_name` | `str` | `"us-west-2"` | AWS region for AgentCore |
| `session_timeout_seconds` | `int` | `900` | Session timeout (max 28800) |
| `max_output_chars` | `int` | `100_000` | Output truncation limit |
| `code_interpreter_identifier` | `str` | `"aws.codeinterpreter.v1"` | Interpreter ID |

AWS credentials are resolved via the standard boto3 credential chain: environment variables, `~/.aws/credentials`, AWS SSO, or IAM role.

## S3Backend Configuration

### Constructor parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bucket` | `str` | required | S3 bucket name |
| `prefix` | `str` | `""` | Key prefix for all objects (e.g. `"agent/workspace/"`) |
| `client` | boto3 S3 client | `None` | Optional pre-configured boto3 client |
| `region_name` | `str` | `None` | AWS region for the default client |

### Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `S3_BACKEND_BUCKET` | Yes (for `from_env()`) | -- | S3 bucket name |
| `S3_BACKEND_PREFIX` | No | `""` | Key prefix for all objects |
| `AWS_REGION` | No | -- | AWS region (checked first; auto-set by AWS Lambda) |
| `AWS_DEFAULT_REGION` | No | -- | AWS region (standard boto3 fallback if `AWS_REGION` is not set) |

AWS credentials are resolved via the standard boto3 credential chain: environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`), shared credentials file (`~/.aws/credentials`), AWS SSO, or IAM role.

## Development

### Setup

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create venv and install all dependencies
uv sync

# Lint
uv run ruff check src/ tests/

# Build
uv build
```

### Testing

The project has two test suites: **unit tests** (mocked S3 via moto) and **integration tests** (real S3 bucket).

#### Unit tests

Unit tests use [moto](https://github.com/getmoto/moto) to mock all S3 API calls. No AWS credentials or network access required.

```bash
uv run pytest
```

This runs 58 tests covering all 8 protocol methods, path helpers, error mapping, `from_env()` factory, and edge cases (binary files, empty files, pagination, partial batch failures).

#### Integration tests

Integration tests run against a **real S3 bucket** to validate actual AWS behavior (pagination, error codes, eventual consistency). They are skipped by default.

**Prerequisites:**

1. An existing S3 bucket with read/write access
2. AWS credentials configured via any standard method:
   - Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
   - Shared credentials file (`~/.aws/credentials`)
   - AWS SSO (`aws sso login`)
   - IAM role (EC2, ECS, Lambda)
3. IAM permissions on the test bucket:
   - `s3:GetObject`
   - `s3:PutObject`
   - `s3:DeleteObject` (for cleanup after tests)
   - `s3:ListBucket`

**Running:**

```bash
S3_TEST_BUCKET=your-bucket-name uv run pytest -m integration
```

Optionally set the region if the bucket is not in `us-east-1`:

```bash
S3_TEST_BUCKET=your-bucket-name AWS_DEFAULT_REGION=us-west-2 uv run pytest -m integration
```

**Run both unit and integration tests together:**

```bash
S3_TEST_BUCKET=your-bucket-name uv run pytest -m ""
```

**Test isolation:** Integration tests create objects under a unique prefix (`integration-test-<uuid>/`) and clean up after themselves. They will not leave artifacts in your bucket.

## License

MIT
