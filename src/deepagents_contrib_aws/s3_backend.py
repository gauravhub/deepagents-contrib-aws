"""S3-backed implementation of the deepagents BackendProtocol.

Maps virtual paths (e.g. /workspace/file.py) to S3 object keys
using a configurable prefix. Uses boto3 for all S3 operations.

Usage:
    from deepagents_contrib_aws import S3Backend

    backend = S3Backend(bucket="my-bucket", prefix="agent/")
    backend = S3Backend.from_env()
"""

from __future__ import annotations

import fnmatch
import logging
import os
from typing import Any

from deepagents.backends.protocol import (
    BackendProtocol,
    EditResult,
    FileDownloadResponse,
    FileInfo,
    FileOperationError,
    FileUploadResponse,
    GlobResult,
    GrepMatch,
    GrepResult,
    LsResult,
    ReadResult,
    WriteResult,
)
from deepagents.backends.utils import (
    create_file_data,
    perform_string_replacement,
)

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None  # type: ignore[assignment]
    ClientError = Exception  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)

_MAX_GREP_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def _path_to_key(path: str, prefix: str) -> str:
    """Convert virtual path /a/b/c to S3 key prefix+a/b/c."""
    path = path.strip("/")
    if not prefix:
        return path
    return f"{prefix}{path}" if path else prefix.rstrip("/")


def _key_to_path(key: str, prefix: str) -> str:
    """Convert S3 key back to virtual path /a/b/c."""
    if prefix and key.startswith(prefix):
        key = key[len(prefix) :]
    key = key.lstrip("/")
    return f"/{key}" if key else "/"


def _map_client_error(err: Any) -> FileOperationError:
    """Map a boto3 ClientError to a standardized FileOperationError code."""
    code = err.response["Error"].get("Code", "")
    if code in ("NoSuchKey", "404"):
        return "file_not_found"
    if code in ("AccessDenied", "Forbidden"):
        return "permission_denied"
    return "invalid_path"


class S3Backend(BackendProtocol):
    """Backend that stores files in an Amazon S3 bucket.

    Implements the deepagents BackendProtocol using boto3 for S3 operations.
    Virtual paths (e.g. ``/workspace/file.py``) are mapped to S3 keys via
    a configurable prefix.

    Args:
        bucket: S3 bucket name.
        prefix: Optional key prefix for all objects (e.g. ``"agent/workspace/"``).
        client: Optional pre-configured boto3 S3 client.
        region_name: Optional AWS region for the default client.
    """

    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        *,
        client: Any | None = None,
        region_name: str | None = None,
    ) -> None:
        if boto3 is None:
            raise ImportError(
                "boto3 is required for S3Backend. "
                "Install with: pip install deepagents-contrib-aws"
            )
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        if self.prefix:
            self.prefix = self.prefix + "/"
        self._client = client or boto3.client("s3", region_name=region_name)
        logger.debug(
            "S3Backend active bucket=%s prefix=%s",
            bucket,
            self.prefix or "(none)",
        )

    @classmethod
    def from_env(
        cls,
        *,
        bucket: str | None = None,
        prefix: str | None = None,
        region_name: str | None = None,
    ) -> S3Backend:
        """Create an S3Backend from environment variables.

        Reads ``S3_BACKEND_BUCKET`` (required), ``S3_BACKEND_PREFIX``
        (optional), and ``AWS_REGION`` or ``AWS_DEFAULT_REGION`` (optional).

        Args:
            bucket: Override for bucket name.
            prefix: Override for key prefix.
            region_name: Override for AWS region.

        Raises:
            ValueError: If bucket is not provided and ``S3_BACKEND_BUCKET``
                is not set.
        """
        bucket = bucket or os.environ.get("S3_BACKEND_BUCKET")
        if not bucket:
            raise ValueError(
                "S3_BACKEND_BUCKET must be set or pass bucket= to S3Backend.from_env()"
            )
        prefix = (
            prefix if prefix is not None else os.environ.get("S3_BACKEND_PREFIX", "")
        )
        region_name = (
            region_name
            or os.environ.get("AWS_REGION")
            or os.environ.get("AWS_DEFAULT_REGION")
        )
        return cls(bucket=bucket, prefix=prefix or "", region_name=region_name)

    def _key(self, path: str) -> str:
        """Convert a virtual path to an S3 key."""
        return _path_to_key(path, self.prefix)

    def _path(self, key: str) -> str:
        """Convert an S3 key to a virtual path."""
        return _key_to_path(key, self.prefix)

    # ── BackendProtocol methods ──────────────────────────────────────

    def ls(self, path: str) -> LsResult:
        """List files and directories at *path*."""
        prefix = self._key(path)
        if prefix and not prefix.endswith("/"):
            prefix = prefix + "/"
        logger.debug("list_objects_v2 bucket=%s prefix=%s", self.bucket, prefix)
        entries: list[FileInfo] = []
        seen: set[str] = set()
        try:
            paginator = self._client.get_paginator("list_objects_v2")
            for page in paginator.paginate(
                Bucket=self.bucket, Prefix=prefix, Delimiter="/"
            ):
                for cp in page.get("CommonPrefixes", []):
                    full_path = self._path(cp["Prefix"])
                    if full_path not in seen:
                        seen.add(full_path)
                        entries.append({"path": full_path, "is_dir": True})
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if key == prefix or (prefix and key == prefix.rstrip("/")):
                        continue
                    full_path = self._path(key)
                    if full_path not in seen:
                        seen.add(full_path)
                        entries.append(
                            {
                                "path": full_path,
                                "is_dir": False,
                                "size": obj.get("Size"),
                                "modified_at": (
                                    obj["LastModified"].isoformat()
                                    if obj.get("LastModified")
                                    else None
                                ),
                            }
                        )
        except ClientError as e:
            return LsResult(error=f"Error listing {path}: {e}")
        return LsResult(entries=entries)

    def read(
        self,
        file_path: str,
        offset: int = 0,
        limit: int = 2000,
    ) -> ReadResult:
        """Read file content with line-based pagination."""
        key = self._key(file_path)
        logger.debug("get_object bucket=%s key=%s", self.bucket, key)
        try:
            resp = self._client.get_object(Bucket=self.bucket, Key=key)
            body = resp["Body"].read().decode("utf-8", errors="replace")
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return ReadResult(error=f"Error: file not found: {file_path}")
            return ReadResult(error=f"Error reading {file_path}: {e}")

        lines = body.splitlines()
        if offset >= len(lines):
            if not lines:
                # Empty file
                last_modified = (
                    resp["LastModified"].isoformat()
                    if resp.get("LastModified")
                    else None
                )
                file_data = create_file_data(
                    content="", created_at=last_modified
                )
                return ReadResult(file_data=file_data)
            return ReadResult(
                error=f"Line offset {offset} exceeds file length ({len(lines)} lines)"
            )

        sliced = lines[offset : offset + limit]
        raw_content = "\n".join(sliced)
        last_modified = (
            resp["LastModified"].isoformat() if resp.get("LastModified") else None
        )
        file_data = create_file_data(content=raw_content, created_at=last_modified)
        return ReadResult(file_data=file_data)

    def write(self, file_path: str, content: str) -> WriteResult:
        """Write content to a new file; error if file already exists."""
        key = self._key(file_path)
        logger.debug("head_object bucket=%s key=%s", self.bucket, key)
        try:
            self._client.head_object(Bucket=self.bucket, Key=key)
            return WriteResult(error=f"File already exists: {file_path}")
        except ClientError as e:
            if e.response["Error"]["Code"] != "404":
                return WriteResult(error=f"Error checking file: {e}")
        logger.debug("put_object bucket=%s key=%s", self.bucket, key)
        try:
            self._client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=content.encode("utf-8"),
                ContentType="text/plain; charset=utf-8",
            )
            return WriteResult(path=file_path, files_update=None)
        except ClientError as e:
            return WriteResult(error=f"Error writing {file_path}: {e}")

    def edit(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,  # noqa: FBT001, FBT002
    ) -> EditResult:
        """Replace *old_string* with *new_string* in an existing file."""
        key = self._key(file_path)
        logger.debug("get_object bucket=%s key=%s", self.bucket, key)
        try:
            resp = self._client.get_object(Bucket=self.bucket, Key=key)
            content = resp["Body"].read().decode("utf-8", errors="replace")
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return EditResult(error=f"File not found: {file_path}")
            return EditResult(error=f"Error reading {file_path}: {e}")

        result = perform_string_replacement(
            content, old_string, new_string, replace_all
        )
        if isinstance(result, str):
            return EditResult(error=result)
        new_content, occurrences = result

        logger.debug("put_object bucket=%s key=%s", self.bucket, key)
        try:
            self._client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=new_content.encode("utf-8"),
                ContentType="text/plain; charset=utf-8",
            )
            return EditResult(
                path=file_path, files_update=None, occurrences=occurrences
            )
        except ClientError as e:
            return EditResult(error=f"Error writing {file_path}: {e}")

    def grep(
        self,
        pattern: str,
        path: str | None = None,
        glob: str | None = None,
    ) -> GrepResult:
        """Search for literal text *pattern* in files."""
        prefix = self._key(path or "/")
        if prefix and not prefix.endswith("/"):
            prefix = prefix + "/"
        logger.debug("list_objects_v2 bucket=%s prefix=%s (grep)", self.bucket, prefix)
        matches: list[GrepMatch] = []
        try:
            paginator = self._client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if obj.get("Size", 0) > _MAX_GREP_FILE_SIZE:
                        continue
                    vpath = self._path(key)
                    if glob and not fnmatch.fnmatch(vpath.lstrip("/"), glob):
                        continue
                    logger.debug("get_object bucket=%s key=%s (grep)", self.bucket, key)
                    try:
                        resp = self._client.get_object(Bucket=self.bucket, Key=key)
                        body = resp["Body"].read().decode("utf-8", errors="replace")
                    except ClientError:
                        continue
                    for i, line in enumerate(body.splitlines(), start=1):
                        if pattern in line:
                            matches.append(
                                {"path": vpath, "line": i, "text": line}
                            )
        except ClientError as e:
            return GrepResult(error=f"Error searching: {e}")
        return GrepResult(matches=matches)

    def glob(self, pattern: str, path: str = "/") -> GlobResult:
        """Find files matching a glob *pattern*."""
        prefix = self._key(path)
        if prefix and not prefix.endswith("/"):
            prefix = prefix + "/"
        logger.debug(
            "list_objects_v2 bucket=%s prefix=%s (glob)", self.bucket, prefix
        )
        file_matches: list[FileInfo] = []
        try:
            paginator = self._client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    vpath = self._path(key)
                    if not fnmatch.fnmatch(vpath.lstrip("/"), pattern):
                        continue
                    file_matches.append(
                        {
                            "path": vpath,
                            "is_dir": False,
                            "size": obj.get("Size"),
                            "modified_at": (
                                obj["LastModified"].isoformat()
                                if obj.get("LastModified")
                                else None
                            ),
                        }
                    )
        except ClientError as e:
            return GlobResult(error=f"Error globbing: {e}")
        return GlobResult(matches=file_matches)

    def upload_files(
        self, files: list[tuple[str, bytes]]
    ) -> list[FileUploadResponse]:
        """Upload multiple files to S3."""
        out: list[FileUploadResponse] = []
        for fpath, content in files:
            key = self._key(fpath)
            logger.debug("put_object bucket=%s key=%s (upload)", self.bucket, key)
            try:
                self._client.put_object(Bucket=self.bucket, Key=key, Body=content)
                out.append(FileUploadResponse(path=fpath, error=None))
            except ClientError as e:
                out.append(FileUploadResponse(path=fpath, error=_map_client_error(e)))
        return out

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        """Download multiple files from S3."""
        out: list[FileDownloadResponse] = []
        for fpath in paths:
            key = self._key(fpath)
            logger.debug("get_object bucket=%s key=%s (download)", self.bucket, key)
            try:
                resp = self._client.get_object(Bucket=self.bucket, Key=key)
                content = resp["Body"].read()
                if resp.get("ContentLength", 0) == 0:
                    content = b""
                out.append(
                    FileDownloadResponse(path=fpath, content=content, error=None)
                )
            except ClientError as e:
                out.append(
                    FileDownloadResponse(
                        path=fpath, content=None, error=_map_client_error(e)
                    )
                )
        return out
