# S3Backend

An S3-backed implementation of the deepagents `BackendProtocol` that persists agent workspace files in Amazon S3. Supports all eight protocol methods: `ls`, `read`, `write`, `edit`, `grep`, `glob`, `upload_files`, `download_files`.

## Installation

```bash
pip install deepagents-contrib-aws
```

S3Backend is included in the base package — no extras required.

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

## Operations

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
result = backend.upload_files([
    ("/a.txt", b"content a"),
    ("/b.txt", b"content b"),
])

# Bulk download
result = backend.download_files(["/a.txt", "/b.txt"])
```

## Configuration Reference

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
| `AWS_DEFAULT_REGION` | No | -- | AWS region (standard boto3 fallback) |

### AWS Credentials

Credentials are resolved via the standard boto3 credential chain:

1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`)
2. Shared credentials file (`~/.aws/credentials`)
3. AWS SSO (`aws sso login`)
4. IAM role (EC2, ECS, Lambda)
