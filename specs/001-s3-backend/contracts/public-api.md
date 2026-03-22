# Public API Contract: S3Backend

## Module: `deepagents_contrib_aws.s3_backend`

### Class: `S3Backend(BackendProtocol)`

```python
class S3Backend(BackendProtocol):
    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        *,
        client: Any | None = None,
        region_name: str | None = None,
    ) -> None: ...

    @classmethod
    def from_env(
        cls,
        *,
        bucket: str | None = None,
        prefix: str | None = None,
        region_name: str | None = None,
    ) -> "S3Backend": ...

    # BackendProtocol methods
    def ls(self, path: str) -> LsResult: ...
    def read(self, file_path: str, offset: int = 0, limit: int = 2000) -> ReadResult: ...
    def write(self, file_path: str, content: str) -> WriteResult: ...
    def edit(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult: ...
    def grep(self, pattern: str, path: str | None = None, glob: str | None = None) -> GrepResult: ...
    def glob(self, pattern: str, path: str = "/") -> GlobResult: ...
    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]: ...
    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]: ...
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `S3_BACKEND_BUCKET` | Yes (for `from_env()`) | — | S3 bucket name |
| `S3_BACKEND_PREFIX` | No | `""` | Key prefix |
| `AWS_REGION` | No | — | AWS region (fallback: `AWS_DEFAULT_REGION`) |

### Re-exports from `deepagents_contrib_aws`

```python
from deepagents_contrib_aws import S3Backend
```

The package `__init__.py` re-exports `S3Backend` for convenience.
