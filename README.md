# deepagents-contrib-aws

AWS backend implementations for the [deepagents](https://github.com/langchain-ai/deepagents) framework.

## Backends

### S3Backend

An S3-backed implementation of the `BackendProtocol` that persists agent workspace files in Amazon S3. Supports all eight protocol methods: `ls`, `read`, `write`, `edit`, `grep`, `glob`, `upload_files`, `download_files`.

## Installation

```bash
pip install deepagents-contrib-aws
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

```python
from deepagents_contrib_aws import S3Backend

# Use env vars but override the prefix
backend = S3Backend.from_env(prefix="custom/prefix/")
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

## Configuration

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
