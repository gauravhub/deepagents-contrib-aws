"""Tests for S3Backend.ls_info()."""

from tests.s3_backend.conftest import TEST_BUCKET, TEST_PREFIX


class TestLsInfo:
    def test_list_files_and_dirs(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}file.txt",
            Body=b"hello",
        )
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}sub/nested.txt",
            Body=b"world",
        )

        result = backend.ls_info("/")
        assert isinstance(result, list)
        paths = {e["path"] for e in result}
        assert "/file.txt" in paths
        assert "/sub/" in paths or "/sub" in paths

    def test_empty_directory(self, backend):
        result = backend.ls_info("/")
        assert result == []

    def test_nested_directory(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}a/b/c.txt",
            Body=b"deep",
        )
        result = backend.ls_info("/a/")
        assert isinstance(result, list)
        paths = {e["path"] for e in result}
        assert any("b" in p for p in paths)

    def test_file_info_has_size_and_modified(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}data.txt",
            Body=b"content",
        )
        result = backend.ls_info("/")
        files = [e for e in result if not e.get("is_dir")]
        assert len(files) == 1
        assert files[0].get("size") is not None
        assert files[0].get("modified_at") is not None

    def test_directories_marked_as_dir(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}dir/file.txt",
            Body=b"x",
        )
        result = backend.ls_info("/")
        dirs = [e for e in result if e.get("is_dir")]
        assert len(dirs) >= 1
