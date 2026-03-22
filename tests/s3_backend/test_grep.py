"""Tests for S3Backend.grep_raw()."""

from tests.s3_backend.conftest import TEST_BUCKET, TEST_PREFIX


class TestGrepRaw:
    def test_literal_match(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}src/main.py",
            Body=b"import boto3\nprint('hi')\n",
        )
        result = backend.grep_raw("boto3")
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["path"] == "/src/main.py"
        assert result[0]["line"] == 1
        assert "boto3" in result[0]["text"]

    def test_no_matches(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}file.txt",
            Body=b"nothing here",
        )
        result = backend.grep_raw("nonexistent_pattern")
        assert isinstance(result, list)
        assert result == []

    def test_glob_filter(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}code.py",
            Body=b"target line",
        )
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}readme.md",
            Body=b"target line",
        )
        result = backend.grep_raw("target", glob="*.py")
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["path"] == "/code.py"

    def test_skip_large_files(self, backend, s3_bucket):
        large_body = b"x" * (10 * 1024 * 1024 + 1)
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}huge.txt",
            Body=large_body,
        )
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}small.txt",
            Body=b"findme",
        )
        result = backend.grep_raw("findme")
        assert isinstance(result, list)
        paths = [m["path"] for m in result]
        assert "/small.txt" in paths
        assert "/huge.txt" not in paths

    def test_search_in_subdirectory(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}a/file.txt",
            Body=b"found",
        )
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}b/file.txt",
            Body=b"found",
        )
        result = backend.grep_raw("found", path="/a/")
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["path"] == "/a/file.txt"
