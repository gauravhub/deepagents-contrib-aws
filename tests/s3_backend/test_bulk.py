"""Tests for S3Backend.upload_files() and download_files()."""

from tests.s3_backend.conftest import TEST_BUCKET, TEST_PREFIX


class TestUploadFiles:
    def test_happy_path_batch(self, backend):
        files = [
            ("/a.txt", b"content a"),
            ("/b.txt", b"content b"),
            ("/c.txt", b"content c"),
        ]
        results = backend.upload_files(files)
        assert len(results) == 3
        for r in results:
            assert r.error is None

    def test_order_preserved(self, backend):
        files = [("/z.txt", b"z"), ("/a.txt", b"a"), ("/m.txt", b"m")]
        results = backend.upload_files(files)
        assert [r.path for r in results] == ["/z.txt", "/a.txt", "/m.txt"]

    def test_empty_input(self, backend):
        results = backend.upload_files([])
        assert results == []


class TestDownloadFiles:
    def test_happy_path_batch(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}x.txt",
            Body=b"x data",
        )
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}y.txt",
            Body=b"y data",
        )

        results = backend.download_files(["/x.txt", "/y.txt"])
        assert len(results) == 2
        assert results[0].content == b"x data"
        assert results[1].content == b"y data"
        assert all(r.error is None for r in results)

    def test_partial_failure(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}exists.txt",
            Body=b"ok",
        )

        results = backend.download_files(["/exists.txt", "/missing.txt"])
        assert len(results) == 2
        assert results[0].error is None
        assert results[0].content == b"ok"
        assert results[1].error == "file_not_found"
        assert results[1].content is None

    def test_order_preserved(self, backend, s3_bucket):
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}a.txt",
            Body=b"a",
        )
        s3_bucket.put_object(
            Bucket=TEST_BUCKET,
            Key=f"{TEST_PREFIX}b.txt",
            Body=b"b",
        )

        results = backend.download_files(["/b.txt", "/a.txt"])
        assert results[0].path == "/b.txt"
        assert results[1].path == "/a.txt"

    def test_empty_input(self, backend):
        results = backend.download_files([])
        assert results == []
