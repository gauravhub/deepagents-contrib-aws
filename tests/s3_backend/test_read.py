"""Tests for S3Backend.read()."""

from tests.s3_backend.conftest import TEST_BUCKET, TEST_PREFIX


class TestRead:
    def test_happy_path(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET, Key=f"{TEST_PREFIX}hello.py", Body=b"print('hello')\n"
        )
        result = backend.read("/hello.py")
        assert result.error is None
        assert result.file_data is not None
        assert "print('hello')" in result.file_data["content"]

    def test_offset_and_limit(self, backend, s3_bucket):
        lines = "\n".join(f"line {i}" for i in range(20))
        s3_bucket.put_object(
            Bucket=TEST_BUCKET, Key=f"{TEST_PREFIX}big.txt", Body=lines.encode()
        )
        result = backend.read("/big.txt", offset=5, limit=3)
        assert result.error is None
        content = result.file_data["content"]
        assert "line 5" in content
        assert "line 7" in content
        assert "line 8" not in content

    def test_file_not_found(self, backend):
        result = backend.read("/nonexistent.txt")
        assert result.error is not None
        assert "not found" in result.error.lower()

    def test_binary_content_utf8_replace(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}binary.bin",
            Body=b"\x80\x81\x82\xff hello",
        )
        result = backend.read("/binary.bin")
        assert result.error is None
        assert result.file_data is not None
        # Should have replacement characters but not crash
        assert "hello" in result.file_data["content"]

    def test_empty_file(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET, Key=f"{TEST_PREFIX}empty.txt", Body=b""
        )
        result = backend.read("/empty.txt")
        assert result.error is None
        assert result.file_data is not None

    def test_offset_beyond_file_length(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET, Key=f"{TEST_PREFIX}short.txt", Body=b"one line"
        )
        result = backend.read("/short.txt", offset=100)
        assert result.error is not None
        assert "offset" in result.error.lower() or "exceeds" in result.error.lower()

    def test_file_data_has_timestamps(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET, Key=f"{TEST_PREFIX}ts.txt", Body=b"data"
        )
        result = backend.read("/ts.txt")
        assert result.file_data["created_at"] is not None
        assert result.file_data["modified_at"] is not None
        assert result.file_data["encoding"] == "utf-8"
