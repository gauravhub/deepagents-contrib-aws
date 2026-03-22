"""Tests for S3Backend.from_env()."""

import pytest
from moto import mock_aws

from deepagents_contrib_aws import S3Backend


class TestFromEnv:
    @mock_aws
    def test_all_env_vars_set(self, monkeypatch):
        monkeypatch.setenv("S3_BACKEND_BUCKET", "my-bucket")
        monkeypatch.setenv("S3_BACKEND_PREFIX", "agent/workspace/")
        monkeypatch.setenv("AWS_REGION", "us-west-2")
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")

        backend = S3Backend.from_env()
        assert backend.bucket == "my-bucket"
        assert backend.prefix == "agent/workspace/"

    def test_missing_bucket_raises(self, monkeypatch):
        monkeypatch.delenv("S3_BACKEND_BUCKET", raising=False)
        with pytest.raises(ValueError, match="S3_BACKEND_BUCKET"):
            S3Backend.from_env()

    @mock_aws
    def test_prefix_defaults_to_empty(self, monkeypatch):
        monkeypatch.setenv("S3_BACKEND_BUCKET", "b")
        monkeypatch.delenv("S3_BACKEND_PREFIX", raising=False)
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")

        backend = S3Backend.from_env()
        assert backend.prefix == ""

    @mock_aws
    def test_region_from_aws_region(self, monkeypatch):
        monkeypatch.setenv("S3_BACKEND_BUCKET", "b")
        monkeypatch.setenv("AWS_REGION", "eu-west-1")
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")

        backend = S3Backend.from_env()
        assert backend.bucket == "b"

    @mock_aws
    def test_region_from_aws_default_region(self, monkeypatch):
        monkeypatch.setenv("S3_BACKEND_BUCKET", "b")
        monkeypatch.delenv("AWS_REGION", raising=False)
        monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-southeast-1")
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")

        backend = S3Backend.from_env()
        assert backend.bucket == "b"

    @mock_aws
    def test_constructor_params_override_env(self, monkeypatch):
        monkeypatch.setenv("S3_BACKEND_BUCKET", "env-bucket")
        monkeypatch.setenv("S3_BACKEND_PREFIX", "env-prefix/")
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")

        backend = S3Backend.from_env(bucket="override-bucket", prefix="override/")
        assert backend.bucket == "override-bucket"
        assert backend.prefix == "override/"
