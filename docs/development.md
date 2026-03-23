# Development Guide

## Prerequisites

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/gauravhub/deepagents-contrib-aws.git
cd deepagents-contrib-aws
uv sync
```

This installs all dependencies including dev tools (pytest, ruff, moto, bedrock-agentcore).

## Project Structure

```
src/deepagents_contrib_aws/
├── __init__.py                 # Package exports (S3Backend, AgentCoreCodeInterpreterSandbox)
├── s3_backend.py               # S3-backed BackendProtocol implementation
├── agentcore_sandbox.py        # AgentCore Code Interpreter SandboxBackendProtocol implementation
└── py.typed                    # PEP 561 marker

tests/
├── test_init.py                # Package-level tests (version, imports)
├── s3_backend/                 # S3Backend test suite (moto-mocked)
│   ├── conftest.py
│   ├── test_read.py, test_write.py, test_edit.py, ...
│   └── test_integration.py    # Real S3 (skipped by default)
└── agentcore_sandbox/          # AgentCore sandbox test suite (mock-based)
    ├── conftest.py
    ├── test_execute.py         # Python/shell execution, routing, truncation
    ├── test_files.py           # Upload/download, text/binary, errors
    ├── test_lifecycle.py       # from_env(), stop(), context manager, IDs
    └── test_integration.py     # Real AgentCore (skipped by default)
```

## Linting

The project uses [ruff](https://docs.astral.sh/ruff/) with a line length of 88:

```bash
# Check for issues
uv run ruff check src/ tests/

# Auto-fix
uv run ruff check --fix src/ tests/
```

## Testing

### Unit tests

Unit tests run with mocked AWS services — no credentials or network access required.

```bash
uv run pytest
```

This runs all unit tests:
- **S3Backend**: 57 tests using [moto](https://github.com/getmoto/moto) to mock S3 API calls
- **AgentCore Sandbox**: 44 tests using `unittest.mock` to mock the CodeInterpreter SDK
- **Package**: 1 test for version/imports

### S3Backend integration tests

Run against a **real S3 bucket** to validate actual AWS behavior. Skipped by default.

**Prerequisites:**

1. An S3 bucket with read/write access
2. AWS credentials configured (env vars, `~/.aws/credentials`, SSO, or IAM role)
3. IAM permissions: `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject`, `s3:ListBucket`

```bash
S3_TEST_BUCKET=your-bucket-name uv run pytest -m integration tests/s3_backend/
```

Set the region if the bucket is not in `us-east-1`:

```bash
S3_TEST_BUCKET=your-bucket AWS_DEFAULT_REGION=us-west-2 uv run pytest -m integration tests/s3_backend/
```

Tests create objects under a unique prefix (`integration-test-<uuid>/`) and clean up after themselves.

### AgentCore Sandbox integration tests

Run against a **real AgentCore Code Interpreter** session. Skipped by default.

**Prerequisites:**

1. AWS credentials with bedrock-agentcore permissions
2. `AGENTCORE_TEST_REGION` environment variable set

```bash
AGENTCORE_TEST_REGION=us-west-2 uv run pytest -m integration tests/agentcore_sandbox/
```

### Running all tests (unit + integration)

```bash
S3_TEST_BUCKET=your-bucket AGENTCORE_TEST_REGION=us-west-2 uv run pytest -m ""
```

## Building

```bash
uv build
```

This produces a wheel and sdist in `dist/`.

## Adding a New Backend

The project follows a consistent pattern for each backend:

1. Create `src/deepagents_contrib_aws/<backend_name>.py` implementing the appropriate protocol (`BackendProtocol` or `SandboxBackendProtocol`)
2. Add a `from_env()` classmethod for environment-based configuration
3. Export from `__init__.py` with a `try/except ImportError` guard if the backend has optional dependencies
4. Create `tests/<backend_name>/` with `conftest.py`, unit tests, and integration tests
5. Add optional dependency to `[project.optional-dependencies]` in `pyproject.toml` if needed
6. Update `docs/` with a dedicated backend guide
