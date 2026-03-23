"""Tests for AgentCoreCodeInterpreterSandbox.execute() method."""

from __future__ import annotations

from unittest.mock import patch

from deepagents_contrib_aws.agentcore_sandbox import (
    AgentCoreCodeInterpreterSandbox,
    _extract_python_from_command,
)
from tests.agentcore_sandbox.conftest import _make_stream_response


class TestPythonExecution:
    """Tests for Python code execution via executeCode."""

    def test_python_code_execution(self, sandbox):
        sb, mock_ci = sandbox
        mock_ci.invoke.return_value = _make_stream_response(
            text="42"
        )

        result = sb.execute('python3 -c "print(42)"')

        assert result.output == "42"
        assert result.exit_code == 0
        assert result.truncated is False
        mock_ci.invoke.assert_called_with(
            "executeCode",
            {"language": "python", "code": "print(42)"},
        )

    def test_python_variable_state_preserved(self, sandbox):
        sb, mock_ci = sandbox
        mock_ci.invoke.side_effect = [
            _make_stream_response(text="42"),
            _make_stream_response(text="42"),
        ]

        sb.execute('python3 -c "x = 42"')
        sb.execute('python3 -c "print(x)"')

        assert mock_ci.invoke.call_count == 2
        for call in mock_ci.invoke.call_args_list:
            assert call[0][0] == "executeCode"

    def test_python_error_returns_exit_code_1(self, sandbox):
        sb, mock_ci = sandbox
        mock_ci.invoke.return_value = _make_stream_response(
            error="NameError: x"
        )

        result = sb.execute('python3 -c "print(x)"')

        assert result.exit_code == 1
        assert "NameError" in result.output


class TestShellExecution:
    """Tests for shell command execution via executeCommand."""

    def test_shell_command_execution(self, sandbox):
        sb, mock_ci = sandbox
        mock_ci.invoke.return_value = _make_stream_response(
            text="hello"
        )

        result = sb.execute("echo hello")

        assert result.output == "hello"
        assert result.exit_code == 0
        mock_ci.invoke.assert_called_with(
            "executeCommand",
            {"command": "echo hello"},
        )

    def test_shell_command_error(self, sandbox):
        sb, mock_ci = sandbox
        mock_ci.invoke.return_value = _make_stream_response(
            error="No such file"
        )

        result = sb.execute("ls /nonexistent")

        assert result.exit_code == 1


class TestCommandRouting:
    """Tests for routing between executeCode and executeCommand."""

    def test_python_extraction_routing(self, sandbox):
        sb, mock_ci = sandbox
        mock_ci.invoke.return_value = _make_stream_response(
            text="ok"
        )

        sb.execute('python3 -c "x=1"')
        assert mock_ci.invoke.call_args[0][0] == "executeCode"

        mock_ci.invoke.reset_mock()

        sb.execute("echo hi")
        assert mock_ci.invoke.call_args[0][0] == "executeCommand"

    def test_extract_python_single_quotes(self):
        result = _extract_python_from_command(
            "python3 -c 'print(1)'"
        )
        assert result == "print(1)"

    def test_extract_python_no_argument(self):
        result = _extract_python_from_command("python3 -c")
        assert result is None

    def test_extract_python_nested_quotes(self):
        result = _extract_python_from_command(
            'python3 -c "print(\\"hello\\")"'
        )
        assert result is not None
        assert "hello" in result


class TestOutputHandling:
    """Tests for output parsing, truncation, and edge cases."""

    def test_output_truncation(self, sandbox):
        sb, mock_ci = sandbox
        sb._max_output_chars = 10
        mock_ci.invoke.return_value = _make_stream_response(
            text="a" * 100
        )

        result = sb.execute("echo aaa")

        assert result.truncated is True
        assert "truncated" in result.output

    def test_empty_output(self, sandbox):
        sb, mock_ci = sandbox
        mock_ci.invoke.return_value = {
            "stream": [{"result": {"content": []}}]
        }

        result = sb.execute("echo test")

        assert result.output == "<no output>"

    def test_empty_command(self, sandbox):
        sb, mock_ci = sandbox

        sb.execute("")

        mock_ci.invoke.assert_called_with(
            "executeCommand",
            {"command": ""},
        )

    def test_mixed_text_and_error_output(self, sandbox):
        sb, mock_ci = sandbox
        mock_ci.invoke.return_value = {
            "stream": [
                {
                    "result": {
                        "content": [
                            {"type": "text", "text": "partial"},
                            {"type": "error", "text": "boom"},
                        ]
                    }
                }
            ]
        }

        result = sb.execute("echo test")

        assert result.exit_code == 1
        assert "partial" in result.output
        assert "boom" in result.output


class TestErrorHandling:
    """Tests for SDK exceptions and session recovery."""

    def test_sdk_exception_wrapped(self, sandbox):
        sb, mock_ci = sandbox
        mock_ci.invoke.side_effect = RuntimeError(
            "connection failed"
        )

        result = sb.execute("echo test")

        assert result.exit_code == 1
        assert "connection failed" in result.output

    def test_session_timeout_recovery(self, sandbox):
        sb, mock_ci = sandbox
        mock_ci.invoke.side_effect = [
            RuntimeError("session expired"),
            _make_stream_response(text="recovered"),
        ]

        result = sb.execute("echo test")

        assert result.exit_code == 0
        assert result.output == "recovered"


class TestSessionLifecycle:
    """Tests for lazy session initialization."""

    def test_lazy_session_init(self, sandbox):
        sb, mock_ci = sandbox
        # Create a fresh sandbox without the fixture's execute
        with patch(
            "deepagents_contrib_aws.agentcore_sandbox"
            ".CodeInterpreter",
            return_value=mock_ci,
        ):
            fresh_sb = AgentCoreCodeInterpreterSandbox(
                region_name="us-east-1",
            )
            assert fresh_sb._client is None

            fresh_sb.execute("echo hello")

            assert fresh_sb._client is not None
