# Data Model: S3 Backend for deepagents

## Entities

### S3Backend

The primary class. Holds configuration and provides all protocol methods.

| Attribute | Type | Description |
|-----------|------|-------------|
| `bucket` | `str` | S3 bucket name |
| `prefix` | `str` | Normalized key prefix (always ends with `/` or empty) |
| `_client` | `boto3.client` | boto3 S3 client instance |

**Factory**: `from_env(bucket?, prefix?, region_name?) -> S3Backend`

### Virtual Path ↔ S3 Key Mapping

| Concept | Format | Example |
|---------|--------|---------|
| Virtual Path | Absolute, starts with `/` | `/workspace/hello.py` |
| S3 Key | Prefix + relative path | `agent/workspace/hello.py` |
| Prefix | Normalized, ends with `/` or empty | `agent/` |

**Conversion functions** (module-level):
- `_path_to_key(path, prefix) -> str`
- `_key_to_path(key, prefix) -> str`

### Protocol Result Types (from deepagents)

All imported from `deepagents.backends.protocol`:

| Type | Fields | Used By |
|------|--------|---------|
| `ReadResult` | `error?, file_data?` | `read()` |
| `WriteResult` | `error?, path?, files_update?` | `write()` |
| `EditResult` | `error?, path?, files_update?, occurrences?` | `edit()` |
| `LsResult` | `error?, entries?` | `ls()` |
| `GrepResult` | `error?, matches?` | `grep()` |
| `GlobResult` | `error?, matches?` | `glob()` |
| `FileUploadResponse` | `path, error?` | `upload_files()` |
| `FileDownloadResponse` | `path, content?, error?` | `download_files()` |
| `FileInfo` | `path, is_dir?, size?, modified_at?` | `ls()`, `glob()` |
| `GrepMatch` | `path, line, text` | `grep()` |
| `FileData` | `content, encoding, created_at, modified_at` | `read()` |

### Error Code Mapping

| S3/boto3 Code | Protocol Code |
|--------------|---------------|
| `NoSuchKey` | `file_not_found` |
| `404` | `file_not_found` |
| `AccessDenied` | `permission_denied` |
| `Forbidden` | `permission_denied` |
| Other `ClientError` | `invalid_path` |

## State & Lifecycle

S3Backend is stateless — all state lives in S3. No lifecycle transitions, no caching, no connection pooling beyond what boto3 manages internally.
