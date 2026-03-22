"""Tests for S3Backend.edit()."""

from tests.s3_backend.conftest import TEST_BUCKET, TEST_PREFIX


class TestEdit:
    def test_single_occurrence(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}code.py",
            Body=b"print('hello')\n",
        )
        result = backend.edit("/code.py", "hello", "world")
        assert result.error is None
        assert result.path == "/code.py"
        assert result.occurrences == 1
        assert result.files_update is None

        # Verify content updated
        resp = s3_bucket.get_object(Bucket=TEST_BUCKET, Key=f"{TEST_PREFIX}code.py")
        assert b"world" in resp["Body"].read()

    def test_replace_all(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}multi.txt",
            Body=b"foo bar foo baz foo",
        )
        result = backend.edit("/multi.txt", "foo", "qux", replace_all=True)
        assert result.error is None
        assert result.occurrences == 3

    def test_zero_occurrences_error(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}no_match.txt",
            Body=b"nothing here",
        )
        result = backend.edit("/no_match.txt", "xyz", "abc")
        assert result.error is not None

    def test_multiple_occurrences_without_replace_all(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}ambiguous.txt",
            Body=b"aa bb aa",
        )
        result = backend.edit("/ambiguous.txt", "aa", "cc")
        assert result.error is not None

    def test_file_not_found(self, backend):
        result = backend.edit("/missing.txt", "a", "b")
        assert result.error is not None
        assert "not found" in result.error.lower()
