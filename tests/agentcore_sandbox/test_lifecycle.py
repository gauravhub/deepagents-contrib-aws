"""Tests for from_env(), stop(), context manager, and ID generation."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from deepagents_contrib_aws.agentcore_sandbox import (
    AgentCoreCodeInterpreterSandbox,
)

_CI_PATCH = (
    "deepagents_contrib_aws.agentcore_sandbox.CodeInterpreter"
)

# Env vars to clear so tests are isolated.
_REGION_VARS = (
    "AGENTCORE_REGION",
    "AWS_REGION",
    "AWS_DEFAULT_REGION",
)
_ALL_VARS = (
    *_REGION_VARS,
    "AGENTCORE_SESSION_TIMEOUT",
    "AGENTCORE_CODE_INTERPRETER_ID",
)


def _clear_env(monkeypatch):
    """Remove all AgentCore/AWS env vars that could leak."""
    for var in _ALL_VARS:
        monkeypatch.delenv(var, raising=False)


# ── from_env() region resolution ─────────────────────────


class TestFromEnvRegion:
    def test_from_env_agentcore_region(self, monkeypatch):
        _clear_env(monkeypatch)
        monkeypatch.setenv("AGENTCORE_REGION", "eu-west-1")
        with patch(_CI_PATCH):
            sb = AgentCoreCodeInterpreterSandbox.from_env()
        assert sb._region == "eu-west-1"

    def test_from_env_aws_region_fallback(self, monkeypatch):
        _clear_env(monkeypatch)
        monkeypatch.setenv("AWS_REGION", "us-east-1")
        with patch(_CI_PATCH):
            sb = AgentCoreCodeInterpreterSandbox.from_env()
        assert sb._region == "us-east-1"

    def test_from_env_aws_default_region_fallback(
        self, monkeypatch
    ):
        _clear_env(monkeypatch)
        monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-south-1")
        with patch(_CI_PATCH):
            sb = AgentCoreCodeInterpreterSandbox.from_env()
        assert sb._region == "ap-south-1"

    def test_from_env_default_region(self, monkeypatch):
        _clear_env(monkeypatch)
        with patch(_CI_PATCH):
            sb = AgentCoreCodeInterpreterSandbox.from_env()
        assert sb._region == "us-west-2"


# ── from_env() other fields ──────────────────────────────


class TestFromEnvFields:
    def test_from_env_timeout(self, monkeypatch):
        _clear_env(monkeypatch)
        monkeypatch.setenv("AGENTCORE_SESSION_TIMEOUT", "3600")
        with patch(_CI_PATCH):
            sb = AgentCoreCodeInterpreterSandbox.from_env()
        assert sb._session_timeout == 3600

    def test_from_env_identifier(self, monkeypatch):
        _clear_env(monkeypatch)
        monkeypatch.setenv(
            "AGENTCORE_CODE_INTERPRETER_ID", "custom.id"
        )
        with patch(_CI_PATCH):
            sb = AgentCoreCodeInterpreterSandbox.from_env()
        assert sb._code_interpreter_id == "custom.id"

    def test_from_env_kwargs_override(self, monkeypatch):
        _clear_env(monkeypatch)
        monkeypatch.setenv("AGENTCORE_REGION", "eu-west-1")
        with patch(_CI_PATCH):
            sb = AgentCoreCodeInterpreterSandbox.from_env(
                region_name="ap-southeast-1",
            )
        assert sb._region == "ap-southeast-1"


# ── from_env() validation ────────────────────────────────


class TestFromEnvValidation:
    def test_from_env_invalid_timeout(self, monkeypatch):
        _clear_env(monkeypatch)
        monkeypatch.setenv("AGENTCORE_SESSION_TIMEOUT", "abc")
        with patch(_CI_PATCH), pytest.raises(ValueError):
            AgentCoreCodeInterpreterSandbox.from_env()

    def test_from_env_timeout_exceeds_max(self, monkeypatch):
        _clear_env(monkeypatch)
        monkeypatch.setenv("AGENTCORE_SESSION_TIMEOUT", "99999")
        with patch(_CI_PATCH), pytest.raises(ValueError):
            AgentCoreCodeInterpreterSandbox.from_env()


# ── stop() ────────────────────────────────────────────────


class TestStop:
    def test_stop_releases_session(self, sandbox):
        sb, mock_ci = sandbox
        sb.execute("echo hi")
        sb.stop()
        mock_ci.stop.assert_called()
        assert sb._client is None
        assert sb._session_id is None

    def test_stop_no_session(self):
        with patch(_CI_PATCH):
            sb = AgentCoreCodeInterpreterSandbox(
                region_name="us-east-1",
            )
        sb.stop()  # should not raise

    def test_stop_twice(self, sandbox):
        sb, mock_ci = sandbox
        sb.execute("echo hi")
        sb.stop()
        sb.stop()  # second call should not raise


# ── Context manager ──────────────────────────────────────


class TestContextManager:
    def test_context_manager(self, sandbox):
        sb, mock_ci = sandbox
        with sb:
            sb.execute("echo hi")
        mock_ci.stop.assert_called()

    def test_context_manager_exception(self, sandbox):
        sb, mock_ci = sandbox
        with pytest.raises(ValueError, match="boom"):
            with sb:
                sb.execute("echo hi")
                raise ValueError("boom")
        mock_ci.stop.assert_called()


# ── ID generation ─────────────────────────────────────────


class TestIdGeneration:
    def test_unique_sandbox_id(self):
        with patch(_CI_PATCH):
            sb1 = AgentCoreCodeInterpreterSandbox(
                region_name="us-east-1",
            )
            sb2 = AgentCoreCodeInterpreterSandbox(
                region_name="us-east-1",
            )
        assert sb1.id != sb2.id

    def test_id_before_session(self):
        with patch(_CI_PATCH):
            sb = AgentCoreCodeInterpreterSandbox(
                region_name="us-east-1",
            )
        assert sb.id.startswith("agentcore-ci-")

    def test_id_after_session(self, sandbox):
        sb, mock_ci = sandbox
        sb.execute("echo hi")
        session_prefix = mock_ci.start.return_value[:8]
        assert session_prefix in sb.id
