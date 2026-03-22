"""Integration tests for S3Backend against a real S3 bucket.

These tests are SKIPPED by default. Run them with:

    uv run pytest -m integration

Requires:
    - AWS credentials configured (env vars, ~/.aws/credentials, or IAM role)
    - S3_TEST_BUCKET env var set to an existing bucket you have write access to

The tests use a unique prefix per run to avoid collisions and clean up
after themselves.
"""

from __future__ import annotations

import os
import uuid

import pytest

from deepagents_contrib_aws import S3Backend

pytestmark = pytest.mark.integration

BUCKET = os.environ.get("S3_TEST_BUCKET", "")
REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


def _skip_if_no_bucket():
    if not BUCKET:
        pytest.skip(
            "S3_TEST_BUCKET not set — skipping integration tests"
        )


@pytest.fixture
def backend():
    """Create an S3Backend with a unique prefix for test isolation."""
    _skip_if_no_bucket()
    prefix = f"integration-test-{uuid.uuid4().hex[:8]}/"
    b = S3Backend(bucket=BUCKET, prefix=prefix, region_name=REGION)
    yield b
    # Cleanup: delete all objects under the test prefix
    import boto3

    client = boto3.client("s3", region_name=REGION)
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            client.delete_object(Bucket=BUCKET, Key=obj["Key"])


class TestIntegrationReadWriteEditLs:
    def test_write_read_edit_ls_roundtrip(self, backend):
        # Write
        w = backend.write("/hello.py", "print('hello')\n")
        assert w.error is None
        assert w.path == "/hello.py"

        # Read (returns formatted string)
        r = backend.read("/hello.py")
        assert isinstance(r, str)
        assert "print('hello')" in r

        # Edit
        e = backend.edit("/hello.py", "hello", "world")
        assert e.error is None
        assert e.occurrences == 1

        # Read again to verify edit
        r2 = backend.read("/hello.py")
        assert "world" in r2

        # Ls
        entries = backend.ls_info("/")
        assert isinstance(entries, list)
        paths = {entry["path"] for entry in entries}
        assert "/hello.py" in paths

    def test_write_prevents_overwrite(self, backend):
        backend.write("/exists.txt", "first")
        w2 = backend.write("/exists.txt", "second")
        assert w2.error is not None
        assert "already exists" in w2.error.lower()


class TestIntegrationSearchOps:
    def test_grep_and_glob(self, backend):
        backend.write("/src/app.py", "import boto3\n")
        backend.write("/src/util.py", "import os\n")
        backend.write("/docs/readme.md", "# Docs\n")

        # Grep
        g = backend.grep_raw("boto3")
        assert isinstance(g, list)
        assert len(g) == 1
        assert g[0]["path"] == "/src/app.py"

        # Glob
        gl = backend.glob_info("*.py")
        assert isinstance(gl, list)
        paths = {m["path"] for m in gl}
        assert "/src/app.py" in paths
        assert "/src/util.py" in paths
        assert "/docs/readme.md" not in paths


class TestIntegrationBulkOps:
    def test_upload_and_download(self, backend):
        files = [
            ("/a.txt", b"content a"),
            ("/b.txt", b"content b"),
        ]
        up = backend.upload_files(files)
        assert all(r.error is None for r in up)

        dl = backend.download_files(
            ["/a.txt", "/b.txt", "/missing.txt"]
        )
        assert dl[0].content == b"content a"
        assert dl[1].content == b"content b"
        assert dl[2].error == "file_not_found"
