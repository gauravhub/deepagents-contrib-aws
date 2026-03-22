"""Tests for S3Backend.write()."""

from tests.s3_backend.conftest import TEST_BUCKET, TEST_PREFIX


class TestWrite:
    def test_create_new_file(self, backend, s3_bucket):
        result = backend.write("/new.txt", "hello world")
        assert result.error is None
        assert result.path == "/new.txt"
        assert result.files_update is None

        # Verify file exists in S3
        resp = s3_bucket.get_object(Bucket=TEST_BUCKET, Key=f"{TEST_PREFIX}new.txt")
        assert resp["Body"].read().decode() == "hello world"

    def test_file_already_exists(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET, Key=f"{TEST_PREFIX}exists.txt", Body=b"old"
        )
        result = backend.write("/exists.txt", "new content")
        assert result.error is not None
        assert "already exists" in result.error.lower()

    def test_empty_content(self, backend, s3_bucket):
        result = backend.write("/empty.txt", "")
        assert result.error is None
        assert result.path == "/empty.txt"

    def test_write_returns_no_files_update(self, backend):
        result = backend.write("/test.txt", "content")
        assert result.files_update is None
