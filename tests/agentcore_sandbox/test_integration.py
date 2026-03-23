"""Integration tests for AgentCore Code Interpreter sandbox.

These tests run against a real AgentCore Code Interpreter session.
They are skipped by default and require:

1. AWS credentials configured (env vars, ~/.aws/credentials, or IAM role)
2. AGENTCORE_TEST_REGION environment variable set (e.g. us-west-2)
3. IAM permissions for bedrock-agentcore operations

Run with:
    AGENTCORE_TEST_REGION=us-west-2 uv run pytest -m integration
"""

from __future__ import annotations

import os

import pytest

from deepagents_contrib_aws.agentcore_sandbox import (
    AgentCoreCodeInterpreterSandbox,
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.environ.get("AGENTCORE_TEST_REGION"),
        reason="AGENTCORE_TEST_REGION not set",
    ),
]


@pytest.fixture
def sandbox():
    """Create a real AgentCore sandbox for integration tests."""
    region = os.environ["AGENTCORE_TEST_REGION"]
    sb = AgentCoreCodeInterpreterSandbox(region_name=region)
    yield sb
    sb.stop()


def test_python_execution(sandbox):
    """Execute Python code and verify output."""
    result = sandbox.execute('python3 -c "print(42)"')
    assert result.exit_code == 0
    assert "42" in result.output


def test_shell_command(sandbox):
    """Execute a shell command and verify output."""
    result = sandbox.execute("echo hello")
    assert result.exit_code == 0
    assert "hello" in result.output


def test_file_round_trip(sandbox):
    """Upload and download text and binary files."""
    text_content = b"hello world"
    binary_content = b"\x89PNG\r\n\x1a\n"

    upload_results = sandbox.upload_files([
        ("/tmp/test.txt", text_content),
        ("/tmp/test.bin", binary_content),
    ])
    assert all(r.error is None for r in upload_results)

    download_results = sandbox.download_files([
        "/tmp/test.txt",
        "/tmp/test.bin",
    ])
    assert download_results[0].content == text_content
    assert download_results[1].content == binary_content


def test_session_lifecycle(sandbox):
    """Start, execute, and stop a session."""
    result = sandbox.execute('python3 -c "print(1)"')
    assert result.exit_code == 0
    sandbox.stop()
    assert sandbox._client is None
