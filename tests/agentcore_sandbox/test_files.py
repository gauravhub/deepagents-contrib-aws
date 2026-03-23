"""Tests for upload_files() and download_files()."""

from __future__ import annotations

import base64


class TestUploadFiles:
    """Tests for AgentCoreCodeInterpreterSandbox.upload_files()."""

    def test_upload_text_file(self, sandbox):
        sb, mock_ci = sandbox
        result = sb.upload_files([("/tmp/test.txt", b"hello")])

        mock_ci.invoke.assert_called_with(
            "writeFiles",
            {"content": [{"path": "tmp/test.txt", "text": "hello"}]},
        )
        assert len(result) == 1
        assert result[0].error is None

    def test_upload_binary_file(self, sandbox):
        sb, mock_ci = sandbox
        data = b"\x89PNG\r\n"
        result = sb.upload_files([("/tmp/image.png", data)])

        expected_blob = base64.b64encode(data).decode()
        mock_ci.invoke.assert_called_with(
            "writeFiles",
            {
                "content": [
                    {"path": "tmp/image.png", "blob": expected_blob}
                ]
            },
        )
        assert len(result) == 1
        assert result[0].error is None

    def test_upload_multiple_files(self, sandbox):
        sb, mock_ci = sandbox
        files = [
            ("/tmp/a.txt", b"aaa"),
            ("/tmp/b.txt", b"bbb"),
        ]
        results = sb.upload_files(files)

        assert len(results) == 2
        assert results[0].error is None
        assert results[1].error is None
        assert mock_ci.invoke.call_count == 2

    def test_upload_error_handling(self, sandbox):
        sb, mock_ci = sandbox
        mock_ci.invoke.side_effect = RuntimeError("boom")

        results = sb.upload_files([("/tmp/fail.txt", b"data")])

        assert len(results) == 1
        assert results[0].error == "permission_denied"

    def test_path_normalization(self, sandbox):
        sb, mock_ci = sandbox
        sb.upload_files([("/absolute/path/file.txt", b"data")])

        mock_ci.invoke.assert_called_with(
            "writeFiles",
            {
                "content": [
                    {"path": "absolute/path/file.txt", "text": "data"}
                ]
            },
        )

    def test_upload_empty_list(self, sandbox):
        sb, _mock_ci = sandbox
        results = sb.upload_files([])
        assert results == []

    def test_upload_invalid_path(self, sandbox):
        sb, _mock_ci = sandbox
        results = sb.upload_files(
            [("/tmp/bad\x00file.txt", b"data")]
        )

        assert len(results) == 1
        assert results[0].error == "invalid_path"


class TestDownloadFiles:
    """Tests for AgentCoreCodeInterpreterSandbox.download_files()."""

    def test_download_text_file(self, sandbox):
        sb, mock_ci = sandbox
        mock_ci.invoke.return_value = {
            "stream": [
                {
                    "result": {
                        "content": [
                            {
                                "type": "resource",
                                "resource": {
                                    "uri": "file://test.txt",
                                    "text": "hello",
                                },
                            }
                        ]
                    }
                }
            ]
        }

        results = sb.download_files(["/test.txt"])

        assert len(results) == 1
        assert results[0].content == b"hello"
        assert results[0].error is None

    def test_download_binary_file(self, sandbox):
        sb, mock_ci = sandbox
        raw = b"\x89PNG"
        mock_ci.invoke.return_value = {
            "stream": [
                {
                    "result": {
                        "content": [
                            {
                                "type": "resource",
                                "resource": {
                                    "uri": "file://image.png",
                                    "blob": base64.b64encode(
                                        raw
                                    ).decode(),
                                },
                            }
                        ]
                    }
                }
            ]
        }

        results = sb.download_files(["/image.png"])

        assert len(results) == 1
        assert results[0].content == b"\x89PNG"
        assert results[0].error is None

    def test_download_file_not_found(self, sandbox):
        sb, mock_ci = sandbox
        mock_ci.invoke.return_value = {"stream": []}

        results = sb.download_files(["/missing.txt"])

        assert len(results) == 1
        assert results[0].error == "file_not_found"
        assert results[0].content is None

    def test_download_multiple_files(self, sandbox):
        sb, mock_ci = sandbox
        text_response = {
            "stream": [
                {
                    "result": {
                        "content": [
                            {
                                "type": "resource",
                                "resource": {
                                    "uri": "file://a.txt",
                                    "text": "hello",
                                },
                            }
                        ]
                    }
                }
            ]
        }
        mock_ci.invoke.side_effect = [
            text_response,
            RuntimeError("gone"),
        ]

        results = sb.download_files(["/a.txt", "/b.txt"])

        assert len(results) == 2
        assert results[0].content == b"hello"
        assert results[0].error is None
        assert results[1].error == "file_not_found"
        assert results[1].content is None
