# deepagents-contrib-aws Development Guidelines

## Project Overview

AWS backend implementations for the [deepagents](https://github.com/langchain-ai/deepagents) framework. Two backends:

- **S3Backend** — `BackendProtocol` implementation storing files in S3
- **AgentCoreCodeInterpreterSandbox** — `SandboxBackendProtocol` implementation executing code via Bedrock AgentCore Code Interpreter

## Tech Stack

- Python >=3.11
- `deepagents>=0.4.0` (PyPI — never depend on unreleased versions)
- `boto3>=1.34.0`
- `bedrock-agentcore`

## Project Structure

```text
src/deepagents_contrib_aws/
├── __init__.py                 # Re-exports S3Backend + AgentCoreCodeInterpreterSandbox (lazy)
├── s3_backend.py               # S3-backed BackendProtocol
├── agentcore_sandbox.py        # AgentCore SandboxBackendProtocol
└── py.typed

tests/
├── test_init.py                # Package-level tests
├── s3_backend/                 # S3 tests (moto-mocked)
└── agentcore_sandbox/          # Sandbox tests (unittest.mock)

docs/
├── s3-backend.md               # S3Backend usage guide
├── agentcore-sandbox.md        # Sandbox usage guide
└── development.md              # Build/test guide
```

## Commands

```bash
uv sync                          # Install all dependencies
uv run pytest                    # Run unit tests (no AWS credentials needed)
uv run ruff check src/ tests/    # Lint
uv build                         # Build package
```

## Code Style

- Ruff with line-length 88
- `from __future__ import annotations` in all files
- Type hints on all public methods
- Follow existing patterns in `s3_backend.py` for new backends

## Key Conventions

- **No local source dependencies** — never add `[tool.uv.sources]` with local paths
- **No exceptions from protocol methods** — `execute()` wraps errors in `ExecuteResponse`; `from_env()` MAY raise `ValueError`
- **AWS env vars** — use `AWS_SESSION_TOKEN` (not legacy `AWS_SECURITY_TOKEN`); test conftest sets 4 vars: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_DEFAULT_REGION`
- **All dependencies are required** — no optional extras; all backends available on install
- **Integration tests** — mark with `@pytest.mark.integration`, skipped by default via `addopts = "-m 'not integration'"`
- **Version** — update in BOTH `pyproject.toml` AND `src/deepagents_contrib_aws/__init__.py`
- **Test organization** — each backend gets its own `tests/<backend_name>/` subfolder

## Active Technologies
- Python 3.11+ + deepagents>=0.4.0, deepagents-contrib-aws>=0.2.0, langchain-anthropic, tavily-python, langgraph, python-dotenv (004-deep-research-agent)
- Amazon S3 via S3Backend (7 route prefixes), AgentCoreCodeInterpreterSandbox (default) (004-deep-research-agent)

## Recent Changes
- 004-deep-research-agent: Added Python 3.11+ + deepagents>=0.4.0, deepagents-contrib-aws>=0.2.0, langchain-anthropic, tavily-python, langgraph, python-dotenv
