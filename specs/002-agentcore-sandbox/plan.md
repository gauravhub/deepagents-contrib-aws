# Implementation Plan: AgentCore Code Interpreter Sandbox

**Branch**: `feature/agentcore-sandbox` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-agentcore-sandbox/spec.md`

## Summary

Implement `AgentCoreCodeInterpreterSandbox`, a `BaseSandbox` subclass that delegates code and command execution to Amazon Bedrock AgentCore Code Interpreter. Unlike the reference implementation (Python-only), this supports both Python (`executeCode`) and shell commands (`executeCommand`). File operations use native AgentCore APIs (`writeFiles`/`readFiles`) instead of Python-snippet workarounds. The sandbox is packaged as an optional extra (`[agentcore]`) in the existing `deepagents-contrib-aws` PyPI package.

## Technical Context

**Language/Version**: Python >=3.11
**Primary Dependencies**: `deepagents>=0.4.0` (BaseSandbox, protocol types), `bedrock-agentcore` (CodeInterpreter client), `boto3>=1.34.0`
**Storage**: N/A (remote AgentCore sessions)
**Testing**: pytest with mocked CodeInterpreter (unittest.mock), integration tests with `@pytest.mark.integration`
**Target Platform**: Linux/macOS (Python library)
**Project Type**: Library (PyPI package extension)
**Performance Goals**: N/A (performance determined by AgentCore service)
**Constraints**: Ruff line-length 88, no local source dependencies, deepagents>=0.4.0 from PyPI only
**Scale/Scope**: Single module (~300 LOC) + 4 test files (~500 LOC)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution is a template with placeholder principles — no concrete gates are defined. No violations to check.

**Post-Phase 1 re-check**: Still no violations. The design follows existing S3Backend patterns established in the codebase.

## Project Structure

### Documentation (this feature)

```text
specs/002-agentcore-sandbox/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0: SDK research, API patterns
├── data-model.md        # Phase 1: Entity model
├── quickstart.md        # Phase 1: Usage examples
├── contracts/
│   └── public-api.md    # Phase 1: Public API contract
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2: Task breakdown (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/deepagents_contrib_aws/
├── __init__.py                    # Add AgentCoreCodeInterpreterSandbox re-export
├── s3_backend.py                  # Existing (unchanged)
├── agentcore_sandbox.py           # NEW: AgentCoreCodeInterpreterSandbox class
└── py.typed                       # Existing (unchanged)

tests/
├── s3_backend/                    # Existing (unchanged)
└── agentcore_sandbox/             # NEW: test suite
    ├── __init__.py
    ├── conftest.py                # Fixtures with mocked CodeInterpreter
    ├── test_execute.py            # Python extraction, shell commands, errors, truncation
    ├── test_files.py              # upload_files, download_files, text/binary, errors
    ├── test_lifecycle.py          # from_env, stop, context manager, lazy init, session timeout
    └── test_integration.py        # @pytest.mark.integration (real AgentCore)
```

**Structure Decision**: Single project layout matching existing `src/` + `tests/` structure. New module added alongside existing `s3_backend.py`.

## Architecture

### Component Design

```
┌─────────────────────────────────────────┐
│  AgentCoreCodeInterpreterSandbox        │
│  (extends BaseSandbox)                  │
│                                         │
│  ┌─────────────┐  ┌──────────────────┐  │
│  │ execute()   │  │ upload_files()   │  │
│  │             │  │ download_files() │  │
│  │ python3 -c? │  └──────────────────┘  │
│  │  ├─ yes: executeCode                 │
│  │  └─ no:  executeCommand              │
│  └─────────────┘                        │
│                                         │
│  ┌──────────────────────────────┐       │
│  │ _ensure_session()            │       │
│  │ Lazy: CodeInterpreter.start()│       │
│  │ Timeout: catch + retry once  │       │
│  └──────────────────────────────┘       │
└─────────────────────────────────────────┘
         │
         ▼
  CodeInterpreter SDK (bedrock-agentcore)
         │
         ▼
  AgentCore Service (remote)
```

### Key Implementation Details

1. **Command routing**: `_extract_python_from_command()` parses `python3 -c "..."` commands. Matches → `executeCode` (preserves Python variable state). Non-matches → `executeCommand` (shell execution).

2. **Response parsing**: Both `executeCode` and `executeCommand` return `{"stream": [{"result": {"content": [...]}}]}`. Parse `content` items: `type: "text"` → output, `type: "error"` → error (set exit_code=1).

3. **File operations**: `upload_files` auto-detects text vs binary — try UTF-8 decode, fallback to base64 `blob`. `download_files` parses `readFiles` response, extracting `resource.text` or decoding `resource.blob`.

4. **Path normalization**: `writeFiles` requires relative paths. Strip leading `/` from paths before sending to AgentCore.

5. **Session timeout recovery**: Wrap `invoke()` in try/except. On exception, attempt `stop()` + `_ensure_session()` + retry once. If retry fails, return error in `ExecuteResponse`.

6. **Optional dependency**: `bedrock-agentcore` imported with `try/except ImportError`. Module-level import in `agentcore_sandbox.py`. In `__init__.py`, use lazy import so `S3Backend` users aren't affected.

### Testing Strategy

- **Unit tests**: Mock `CodeInterpreter` at the class level using `unittest.mock.patch`. Mock `start()`, `invoke()`, `stop()`. Configure `invoke()` return values to simulate various response formats.
- **conftest.py**: Fixtures provide pre-configured mocks and sandbox instances. Set 4 AWS env vars (no legacy `AWS_SECURITY_TOKEN`).
- **Integration tests**: `@pytest.mark.integration`, require real AWS credentials and AgentCore access. Test real Python execution, shell commands, file round-trips.

### Package Changes

1. **pyproject.toml**:
   - Add `[project.optional-dependencies]` with `agentcore = ["bedrock-agentcore"]`
   - Add `"bedrock-agentcore"` to dev dependency group
   - Update integration test marker description

2. **__init__.py**:
   - Add lazy import of `AgentCoreCodeInterpreterSandbox`
   - Update `__all__` to include new class
   - Bump `__version__`

3. **pyproject.toml version**: Bump version

4. **README.md**: Add AgentCore sandbox section with usage docs

## Complexity Tracking

No constitution violations to justify — the design follows established patterns.
