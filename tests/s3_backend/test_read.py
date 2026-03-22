"""Tests for S3Backend.read()."""

from tests.s3_backend.conftest import TEST_BUCKET, TEST_PREFIX


class TestRead:
    def test_happy_path(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}hello.py",
            Body=b"print('hello')\n",
        )
        result = backend.read("/hello.py")
        assert isinstance(result, str)
        assert "print('hello')" in result

    def test_offset_and_limit(self, backend, s3_bucket):
        lines = "\n".join(f"line {i}" for i in range(20))
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}big.txt",
            Body=lines.encode(),
        )
        result = backend.read("/big.txt", offset=5, limit=3)
        assert "line 5" in result
        assert "line 7" in result
        assert "line 8" not in result

    def test_file_not_found(self, backend):
        result = backend.read("/nonexistent.txt")
        assert "not found" in result.lower() or "error" in result.lower()

    def test_binary_content_utf8_replace(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}binary.bin",
            Body=b"\x80\x81\x82\xff hello",
        )
        result = backend.read("/binary.bin")
        assert isinstance(result, str)
        assert "hello" in result

    def test_empty_file(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}empty.txt",
            Body=b"",
        )
        result = backend.read("/empty.txt")
        assert isinstance(result, str)
        assert result == ""

    def test_offset_beyond_file_length(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}short.txt",
            Body=b"one line",
        )
        result = backend.read("/short.txt", offset=100)
        assert result == ""

    def test_line_numbers_in_output(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}numbered.txt",
            Body=b"first\nsecond\nthird",
        )
        result = backend.read("/numbered.txt")
        # format_content_with_line_numbers adds line numbers
        assert "1" in result
        assert "first" in result
