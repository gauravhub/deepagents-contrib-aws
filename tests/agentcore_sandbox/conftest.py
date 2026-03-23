"""Shared pytest fixtures for AgentCore sandbox tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from deepagents_contrib_aws.agentcore_sandbox import (
    AgentCoreCodeInterpreterSandbox,
)

TEST_REGION = "us-east-1"
TEST_SESSION_ID = "sess-abc12345"


def _make_stream_response(
    text: str | None = None,
    error: str | None = None,
) -> dict:
    """Build a mock AgentCore stream response dict."""
    content: list[dict] = []
    if text is not None:
        content.append({"type": "text", "text": text})
    if error is not None:
        content.append({"type": "error", "text": error})
    return {
        "stream": [{"result": {"content": content}}],
    }


@pytest.fixture
def aws_env(monkeypatch):
    """Set up mock AWS environment variables."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", TEST_REGION)


@pytest.fixture
def mock_code_interpreter():
    """Create a mock CodeInterpreter instance."""
    mock_ci = MagicMock()
    mock_ci.start.return_value = TEST_SESSION_ID
    mock_ci.invoke.return_value = _make_stream_response(
        text="default output"
    )
    mock_ci.stop.return_value = True
    return mock_ci


@pytest.fixture
def sandbox(aws_env, mock_code_interpreter):
    """Create a sandbox with a mocked CodeInterpreter."""
    with patch(
        "deepagents_contrib_aws.agentcore_sandbox"
        ".CodeInterpreter",
        return_value=mock_code_interpreter,
    ):
        sb = AgentCoreCodeInterpreterSandbox(
            region_name=TEST_REGION,
            session_timeout_seconds=900,
            max_output_chars=100_000,
        )
        yield sb, mock_code_interpreter
