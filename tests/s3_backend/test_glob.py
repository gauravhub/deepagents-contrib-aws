"""Tests for S3Backend.glob_info()."""

from tests.s3_backend.conftest import TEST_BUCKET, TEST_PREFIX


class TestGlobInfo:
    def test_wildcard_match(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}main.py",
            Body=b"x",
        )
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}utils.py",
            Body=b"x",
        )
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}readme.md",
            Body=b"x",
        )

        result = backend.glob_info("*.py")
        assert isinstance(result, list)
        paths = {m["path"] for m in result}
        assert "/main.py" in paths
        assert "/utils.py" in paths
        assert "/readme.md" not in paths

    def test_no_matches(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}file.txt",
            Body=b"x",
        )
        result = backend.glob_info("*.xyz")
        assert result == []

    def test_base_path_filtering(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}src/a.py",
            Body=b"x",
        )
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}docs/b.py",
            Body=b"x",
        )
        result = backend.glob_info("*.py", path="/src/")
        paths = {m["path"] for m in result}
        assert "/src/a.py" in paths
        assert "/docs/b.py" not in paths

    def test_file_info_fields(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}data.txt",
            Body=b"content",
        )
        result = backend.glob_info("*.txt")
        assert len(result) == 1
        entry = result[0]
        assert entry["is_dir"] is False
        assert entry.get("size") is not None
