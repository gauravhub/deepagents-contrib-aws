"""Shared pytest fixtures for S3Backend tests."""

from __future__ import annotations

import boto3
import pytest
from moto import mock_aws

from deepagents_contrib_aws import S3Backend

TEST_BUCKET = "test-bucket"
TEST_PREFIX = "test/"
TEST_REGION = "us-east-1"


@pytest.fixture
def aws_env(monkeypatch):
    """Set up mock AWS environment variables."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", TEST_REGION)


@pytest.fixture
def s3_client(aws_env):
    """Create a moto-mocked boto3 S3 client."""
    with mock_aws():
        client = boto3.client("s3", region_name=TEST_REGION)
        yield client


@pytest.fixture
def s3_bucket(s3_client):
    """Create a test S3 bucket and return the client."""
    s3_client.create_bucket(Bucket=TEST_BUCKET)
    return s3_client


@pytest.fixture
def backend(s3_bucket):
    """Create an S3Backend instance with the mocked S3 bucket."""
    return S3Backend(
        bucket=TEST_BUCKET,
        prefix=TEST_PREFIX,
        client=s3_bucket,
    )
