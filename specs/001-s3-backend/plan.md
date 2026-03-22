# Implementation Plan: S3 Backend for deepagents

**Branch**: `001-s3-backend` | **Date**: 2026-03-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-s3-backend/spec.md`

## Summary

Implement an S3-backed `BackendProtocol` for the deepagents framework as a standalone PyPI package (`deepagents-contrib-aws`). The implementation translates virtual file paths to S3 object keys via a configurable prefix, using boto3 for all S3 operations. All eight protocol methods are implemented synchronously with proper result objects. A working reference implementation exists and will be improved for production quality — notably upgrading from deprecated method names (`ls_info`/`grep_raw`/`glob_info` → `ls`/`grep`/`glob`) and returning proper `ReadResult` dataclasses instead of raw strings.

## Technical Context

**Language/Version**: Python >=3.11
**Primary Dependencies**: boto3 >=1.34.0, deepagents (for BackendProtocol, result types, utilities)
**Storage**: Amazon S3 (standard or Express One Zone)
**Testing**: pytest with moto[s3] for S3 mocking
**Target Platform**: Any platform with Python and AWS access
**Project Type**: Library (PyPI package)
**Build System**: hatchling with src/ layout, managed by uv
**Performance Goals**: N/A — bounded by S3 API latency
**Constraints**: All methods sync; async via protocol default `asyncio.to_thread`. No exceptions to callers.
**Scale/Scope**: Single class (~400 LOC), ~200 LOC tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution is a template (not customized for this project). No gates to enforce. Proceeding.

## Project Structure

### Documentation (this feature)

```text
specs/001-s3-backend/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/deepagents_contrib_aws/
├── __init__.py          # Package init, re-exports S3Backend, __version__
├── s3_backend.py        # S3Backend class implementing BackendProtocol
└── py.typed             # PEP 561 marker

tests/
├── __init__.py
├── test_s3_backend.py   # Unit tests for all protocol methods
└── test_init.py         # Existing smoke test
```

**Structure Decision**: Single-project src/ layout. No web/mobile/CLI layers — this is a pure library package.

## Architecture

### Key Design Decisions

1. **Use current protocol method names** (`ls`, `grep`, `glob`) — NOT the deprecated `ls_info`, `grep_raw`, `glob_info` from the reference. The upstream protocol provides backwards-compat shims, but new implementations should use the current names directly.

2. **Return proper result dataclasses** — The reference `read()` returns raw strings. Our implementation returns `ReadResult(file_data=FileData(...))` as specified by the protocol. Similarly, `ls()` returns `LsResult`, `grep()` returns `GrepResult`, `glob()` returns `GlobResult`.

3. **Reuse upstream utilities** — `format_content_with_line_numbers()` and `perform_string_replacement()` from `deepagents.backends.utils` are well-tested. Use them rather than reimplementing.

4. **No logging infrastructure** — The reference has colored S3 API logging. For a production library package, omit custom colored loggers and rely on standard `logging.getLogger(__name__)` at DEBUG level. Users can configure logging as needed.

5. **Error mapping centralized** — A single `_map_client_error(e: ClientError) -> FileOperationError` helper to consistently map boto3 errors to protocol error codes.

### Method Implementation Map

| Protocol Method | S3 API Calls | Return Type | Key Notes |
|----------------|-------------|-------------|-----------|
| `ls(path)` | `list_objects_v2` (paginated, delimiter `/`) | `LsResult` | CommonPrefixes → dirs, Contents → files, skip self-refs |
| `read(path, offset, limit)` | `get_object` | `ReadResult` | UTF-8 decode w/ replace, line pagination, return FileData |
| `write(path, content)` | `head_object` + `put_object` | `WriteResult` | Error if exists, `files_update=None` (external storage) |
| `edit(path, old, new, replace_all)` | `get_object` + `put_object` | `EditResult` | Use `perform_string_replacement()`, return occurrences |
| `grep(pattern, path, glob)` | `list_objects_v2` + `get_object` per file | `GrepResult` | Literal search, skip >10MB, fnmatch glob filter |
| `glob(pattern, path)` | `list_objects_v2` (paginated) | `GlobResult` | fnmatch filtering on virtual paths |
| `upload_files(files)` | `put_object` per file | `list[FileUploadResponse]` | Per-file error handling, preserve order |
| `download_files(paths)` | `get_object` per file | `list[FileDownloadResponse]` | Per-file error handling, preserve order |

### Path Handling

```
Virtual Path:  /workspace/file.py
                    ↓ _path_to_key(path, prefix="agent/")
S3 Key:        agent/workspace/file.py
                    ↓ _key_to_path(key, prefix="agent/")
Virtual Path:  /workspace/file.py
```

- Prefix normalized to end with `/` (or empty string)
- Virtual paths always start with `/`
- Helper functions are module-level (testable independently)

### Error Handling Strategy

| boto3 Error Code | Protocol Error Code |
|-----------------|-------------------|
| `NoSuchKey` | `file_not_found` |
| `404` (head_object) | `file_not_found` |
| `AccessDenied`, `Forbidden` | `permission_denied` |
| Other `ClientError` | `invalid_path` |

All errors captured in result objects. No exceptions propagate to callers.

### Dependencies (pyproject.toml updates)

```toml
[project]
dependencies = [
    "boto3>=1.34.0",
    "deepagents",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff>=0.4",
    "moto[s3]>=5.0",
]
```

## Complexity Tracking

No constitution violations to justify.
