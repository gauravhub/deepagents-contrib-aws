"""Tests for path conversion helpers."""

from deepagents_contrib_aws.s3_backend import _key_to_path, _path_to_key


class TestPathToKey:
    def test_with_prefix(self):
        assert _path_to_key("/workspace/file.py", "agent/") == "agent/workspace/file.py"

    def test_without_prefix(self):
        assert _path_to_key("/workspace/file.py", "") == "workspace/file.py"

    def test_root_path_with_prefix(self):
        assert _path_to_key("/", "agent/") == "agent"

    def test_root_path_without_prefix(self):
        assert _path_to_key("/", "") == ""

    def test_trailing_slash_in_prefix(self):
        assert _path_to_key("/file.py", "pfx/") == "pfx/file.py"

    def test_no_trailing_slash_in_prefix(self):
        assert _path_to_key("/file.py", "pfx") == "pfxfile.py"

    def test_nested_path(self):
        assert _path_to_key("/a/b/c/d.txt", "p/") == "p/a/b/c/d.txt"

    def test_dotdot_in_path(self):
        # Path helpers do not sanitize — they convert as-is
        result = _path_to_key("/../etc/passwd", "agent/")
        assert "etc/passwd" in result


class TestKeyToPath:
    def test_with_prefix(self):
        assert _key_to_path("agent/workspace/file.py", "agent/") == "/workspace/file.py"

    def test_without_prefix(self):
        assert _key_to_path("workspace/file.py", "") == "/workspace/file.py"

    def test_root_key_with_prefix(self):
        assert _key_to_path("agent/", "agent/") == "/"

    def test_empty_key(self):
        assert _key_to_path("", "") == "/"

    def test_key_not_matching_prefix(self):
        assert _key_to_path("other/file.py", "agent/") == "/other/file.py"

    def test_nested_key(self):
        assert _key_to_path("p/a/b/c.txt", "p/") == "/a/b/c.txt"
