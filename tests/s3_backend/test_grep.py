"""Tests for S3Backend.grep()."""

from tests.s3_backend.conftest import TEST_BUCKET, TEST_PREFIX


class TestGrep:
    def test_literal_match(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}src/main.py",
            Body=b"import boto3\nprint('hi')\n",
        )
        result = backend.grep("boto3")
        assert result.error is None
        assert len(result.matches) == 1
        assert result.matches[0]["path"] == "/src/main.py"
        assert result.matches[0]["line"] == 1
        assert "boto3" in result.matches[0]["text"]

    def test_no_matches(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET, Key=f"{TEST_PREFIX}file.txt", Body=b"nothing here"
        )
        result = backend.grep("nonexistent_pattern")
        assert result.error is None
        assert result.matches == []

    def test_glob_filter(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET, Key=f"{TEST_PREFIX}code.py", Body=b"target line"
        )
        s3_bucket.put_object(
            Bucket=TEST_BUCKET, Key=f"{TEST_PREFIX}readme.md", Body=b"target line"
        )
        result = backend.grep("target", glob="*.py")
        assert result.error is None
        assert len(result.matches) == 1
        assert result.matches[0]["path"] == "/code.py"

    def test_skip_large_files(self, backend, s3_bucket):
        # Create a file > 10MB
        large_body = b"x" * (10 * 1024 * 1024 + 1)
        s3_bucket.put_object(
            Bucket=TEST_BUCKET, Key=f"{TEST_PREFIX}huge.txt", Body=large_body
        )
        s3_bucket.put_object(
            Bucket=TEST_BUCKET, Key=f"{TEST_PREFIX}small.txt", Body=b"findme"
        )
        result = backend.grep("findme")
        assert result.error is None
        # Should only find in small.txt, not huge.txt
        paths = [m["path"] for m in result.matches]
        assert "/small.txt" in paths
        assert "/huge.txt" not in paths

    def test_search_in_subdirectory(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET, Key=f"{TEST_PREFIX}a/file.txt", Body=b"found"
        )
        s3_bucket.put_object(
            Bucket=TEST_BUCKET, Key=f"{TEST_PREFIX}b/file.txt", Body=b"found"
        )
        result = backend.grep("found", path="/a/")
        assert result.error is None
        assert len(result.matches) == 1
        assert result.matches[0]["path"] == "/a/file.txt"
