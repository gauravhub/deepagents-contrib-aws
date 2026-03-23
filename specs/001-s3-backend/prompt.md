# S3Backend Feature Prompt

## Feature Description

Implement an S3-based backend for the [deepagents](https://github.com/langchain-ai/deepagents) framework by implementing the `BackendProtocol` interface. This package (`deepagents-contrib-aws`) will be published to PyPI as a standalone installable package.

## Context

The deepagents framework defines a `BackendProtocol` (in `deepagents.backends.protocol`) that abstracts file operations. Existing implementations include `FilesystemBackend`, `StateBackend`, `StoreBackend`, and `CompositeBackend`. We are building an S3-backed implementation that uses Amazon S3 as persistent file storage.

**Upstream protocol definition**: `deepagents.backends.protocol` (available in deepagents>=0.4.0 on PyPI)

## Requirements

### Core
- Implement all `BackendProtocol` methods: `ls`, `read`, `write`, `edit`, `grep`, `glob`, `upload_files`, `download_files`
- Use **boto3** as the AWS SDK
- All sync methods; async variants inherit from protocol defaults (`asyncio.to_thread`)
- Return proper result objects (`ReadResult`, `WriteResult`, `EditResult`, `LsResult`, `GrepResult`, `GlobResult`, `FileUploadResponse`, `FileDownloadResponse`) as defined in the protocol
- Use standardized error codes from `FileOperationError` literals (`file_not_found`, `permission_denied`, `is_directory`, `invalid_path`)

### Constructor & Configuration
- Constructor accepts: `bucket: str`, `prefix: str = ""`, optional `client` (boto3 S3 client), optional `region_name: str`
- `from_env()` classmethod factory reading from environment variables: `S3_BACKEND_BUCKET`, `S3_BACKEND_PREFIX`, `AWS_REGION`/`AWS_DEFAULT_REGION`
- Proper prefix normalization (trailing slash)

### S3 → Protocol Method Mapping
| Protocol Method | S3 API | Notes |
|---|---|---|
| `ls(path)` | `list_objects_v2` with delimiter `/` | Return `FileInfo` with `is_dir`, `size`, `modified_at` |
| `read(path, offset, limit)` | `get_object` | UTF-8 decode with `errors='replace'`, line-based pagination |
| `write(path, content)` | `head_object` + `put_object` | Prevent overwrite (error if exists) |
| `edit(path, old, new, replace_all)` | `get_object` + `put_object` | String replacement with occurrence validation |
| `grep(pattern, path, glob)` | `list_objects_v2` + `get_object` | Literal search, skip files >10MB |
| `glob(pattern, path)` | `list_objects_v2` | `fnmatch` filtering |
| `upload_files(files)` | `put_object` | Batch with per-file error handling |
| `download_files(paths)` | `get_object` | Batch with per-file error handling |

### Path Handling
- Virtual paths start with `/` (e.g., `/workspace/file.py`)
- Internal helpers `_path_to_key()` and `_key_to_path()` convert between virtual paths and S3 keys using the configured prefix

### Error Handling
- Map `botocore.exceptions.ClientError` codes to `FileOperationError` literals
- `NoSuchKey` → `file_not_found`
- `AccessDenied`/`Forbidden` → `permission_denied`
- Return errors in result objects, never raise exceptions to callers

### Package Structure
```
src/deepagents_contrib_aws/
├── __init__.py
├── s3_backend.py          # S3Backend class
└── py.typed
tests/
├── test_s3_backend.py     # Unit tests with mocked boto3
```

### Testing
- Unit tests using `pytest` with mocked boto3 (`unittest.mock` or `moto`)
- Test all protocol methods: happy path + error cases
- Test path conversion helpers
- Test `from_env()` factory

### Dependencies
- Add `boto3>=1.34.0` to project dependencies in `pyproject.toml`
- Add `deepagents` as a dependency for protocol imports
- Add `moto[s3]` as a dev dependency for testing

### Quality
- Type hints on all public methods
- Docstrings on the class and public methods
- Ruff-clean code (already configured in pyproject.toml)
