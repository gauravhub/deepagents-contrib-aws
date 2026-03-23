"""AgentCore Code Interpreter sandbox backend for deepagents.

Extends BaseSandbox to execute code and commands via Amazon Bedrock
AgentCore Code Interpreter. Supports both Python (executeCode) and
shell commands (executeCommand), with native file upload/download.

Requires: pip install deepagents-contrib-aws[agentcore]
"""

from __future__ import annotations

import base64
import logging
import os
import re
import uuid

from deepagents.backends.protocol import (
    ExecuteResponse,
    FileDownloadResponse,
    FileUploadResponse,
)
from deepagents.backends.sandbox import BaseSandbox

try:
    from bedrock_agentcore.tools.code_interpreter_client import (
        CodeInterpreter,
    )
except ImportError:
    CodeInterpreter = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)


def _extract_python_from_command(command: str) -> str | None:
    """Extract Python code from ``python3 -c "..."`` commands.

    Returns the inner code string, or ``None`` if the command does
    not match the ``python3 -c`` pattern.
    """
    command = command.strip()
    m = re.match(r"python3\s+-c\s+([\"'])(.*)$", command, re.DOTALL)
    if not m:
        return None
    quote = m.group(1)
    rest = m.group(2)
    i = 0
    while i < len(rest):
        if rest[i] == "\\" and i + 1 < len(rest):
            i += 2
            continue
        if rest[i] == quote:
            return rest[:i].encode().decode("unicode_escape")
        i += 1
    return None


def _parse_stream_output(
    response: dict,
    max_output_chars: int,
) -> tuple[str, int, bool]:
    """Parse an AgentCore stream response into output text.

    Returns ``(output, exit_code, truncated)``.
    """
    output_parts: list[str] = []
    exit_code = 0
    for event in response.get("stream", []):
        result = event.get("result", {})
        for item in result.get("content", []):
            if item.get("type") == "text":
                output_parts.append(item.get("text", ""))
            if item.get("type") == "error":
                output_parts.append(
                    item.get("text", "Unknown error")
                )
                exit_code = 1
    output = (
        "\n".join(output_parts) if output_parts else "<no output>"
    )
    truncated = False
    if len(output) > max_output_chars:
        output = (
            output[:max_output_chars]
            + "\n\n... Output truncated at "
            + f"{max_output_chars} characters."
        )
        truncated = True
    return output, exit_code, truncated


class AgentCoreCodeInterpreterSandbox(BaseSandbox):
    """Sandbox that runs code via AgentCore Code Interpreter.

    Supports both ``python3 -c "..."`` commands (routed to
    ``executeCode``, preserving variable state) and arbitrary shell
    commands (routed to ``executeCommand``).

    File operations use native AgentCore ``writeFiles``/``readFiles``
    APIs for efficient text and binary transfers.

    Args:
        region_name: AWS region (default ``"us-west-2"``).
        session_timeout_seconds: Session timeout (default 900,
            max 28800).
        max_output_chars: Truncate output above this limit
            (default 100_000).
        code_interpreter_identifier: Interpreter ID
            (default ``"aws.codeinterpreter.v1"``).
    """

    def __init__(
        self,
        region_name: str = "us-west-2",
        session_timeout_seconds: int = 900,
        max_output_chars: int = 100_000,
        code_interpreter_identifier: str = (
            "aws.codeinterpreter.v1"
        ),
    ) -> None:
        if CodeInterpreter is None:
            raise ImportError(
                "bedrock-agentcore is required for "
                "AgentCoreCodeInterpreterSandbox. Install with: "
                "pip install deepagents-contrib-aws[agentcore]"
            )
        self._region = region_name
        self._session_timeout = session_timeout_seconds
        self._max_output_chars = max_output_chars
        self._code_interpreter_id = code_interpreter_identifier
        self._client: CodeInterpreter | None = None
        self._session_id: str | None = None
        self._sandbox_id = f"agentcore-ci-{uuid.uuid4().hex[:8]}"

    @classmethod
    def from_env(
        cls,
        *,
        region_name: str | None = None,
        session_timeout_seconds: int | None = None,
        code_interpreter_identifier: str | None = None,
    ) -> AgentCoreCodeInterpreterSandbox:
        """Create a sandbox from environment variables.

        Reads ``AGENTCORE_REGION`` (or ``AWS_REGION`` /
        ``AWS_DEFAULT_REGION``), ``AGENTCORE_SESSION_TIMEOUT``,
        and ``AGENTCORE_CODE_INTERPRETER_ID``.  Keyword arguments
        take precedence over environment variables.

        Raises:
            ValueError: If timeout is not a valid integer or
                exceeds 28800.
        """
        region = (
            region_name
            or os.environ.get("AGENTCORE_REGION")
            or os.environ.get("AWS_REGION")
            or os.environ.get("AWS_DEFAULT_REGION")
            or "us-west-2"
        )
        timeout_raw = (
            session_timeout_seconds
            if session_timeout_seconds is not None
            else os.environ.get("AGENTCORE_SESSION_TIMEOUT")
        )
        if timeout_raw is not None:
            try:
                timeout = int(timeout_raw)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"AGENTCORE_SESSION_TIMEOUT must be an "
                    f"integer, got: {timeout_raw!r}"
                ) from exc
            if timeout > 28800:
                raise ValueError(
                    f"session_timeout_seconds must be <= 28800,"
                    f" got: {timeout}"
                )
        else:
            timeout = 900

        identifier = (
            code_interpreter_identifier
            or os.environ.get("AGENTCORE_CODE_INTERPRETER_ID")
            or "aws.codeinterpreter.v1"
        )
        return cls(
            region_name=region,
            session_timeout_seconds=timeout,
            code_interpreter_identifier=identifier,
        )

    # ── Properties ────────────────────────────────────────────

    @property
    def id(self) -> str:
        """Unique identifier for this sandbox instance."""
        if self._session_id:
            return f"agentcore-ci-{self._session_id[:8]}"
        return self._sandbox_id

    # ── Session management ────────────────────────────────────

    def _ensure_session(self) -> None:
        """Start a CodeInterpreter session if not already active."""
        if self._client is None:
            self._client = CodeInterpreter(
                self._region,
                integration_source="deepagents",
            )
            session_id = self._client.start(
                identifier=self._code_interpreter_id,
                session_timeout_seconds=self._session_timeout,
            )
            self._session_id = session_id or "started"

    def stop(self) -> None:
        """Stop the Code Interpreter session."""
        if self._client is not None:
            try:
                self._client.stop()
            except Exception:
                pass
            self._client = None
            self._session_id = None

    def __enter__(self) -> AgentCoreCodeInterpreterSandbox:
        return self

    def __exit__(self, *args: object) -> None:
        self.stop()

    # ── execute() ─────────────────────────────────────────────

    def execute(self, command: str) -> ExecuteResponse:
        """Execute a command in the sandbox.

        ``python3 -c "..."`` commands are routed to ``executeCode``
        (preserving Python variable state).  All other commands are
        routed to ``executeCommand`` (shell execution).

        Never raises — errors are wrapped in the response.
        """
        self._ensure_session()
        code = _extract_python_from_command(command)
        if code is not None:
            method = "executeCode"
            params = {"language": "python", "code": code}
        else:
            method = "executeCommand"
            params = {"command": command}

        try:
            response = self._client.invoke(method, params)
            output, exit_code, truncated = _parse_stream_output(
                response, self._max_output_chars
            )
            return ExecuteResponse(
                output=output,
                exit_code=exit_code,
                truncated=truncated,
            )
        except Exception as exc:
            logger.debug(
                "invoke(%s) failed, attempting session recovery: "
                "%s",
                method,
                exc,
            )
            try:
                self.stop()
                self._ensure_session()
                response = self._client.invoke(method, params)
                output, exit_code, truncated = (
                    _parse_stream_output(
                        response, self._max_output_chars
                    )
                )
                return ExecuteResponse(
                    output=output,
                    exit_code=exit_code,
                    truncated=truncated,
                )
            except Exception as retry_exc:
                return ExecuteResponse(
                    output=(
                        "Error invoking Code Interpreter: "
                        f"{retry_exc}"
                    ),
                    exit_code=1,
                    truncated=False,
                )

    # ── File operations ───────────────────────────────────────

    def upload_files(
        self, files: list[tuple[str, bytes]]
    ) -> list[FileUploadResponse]:
        """Upload files using the native ``writeFiles`` API."""
        if not files:
            return []
        self._ensure_session()
        results: list[FileUploadResponse] = []
        for path, content in files:
            try:
                if "\x00" in path:
                    results.append(
                        FileUploadResponse(
                            path=path, error="invalid_path"
                        )
                    )
                    continue
                rel_path = path.lstrip("/") or path
                try:
                    text = content.decode("utf-8")
                    file_entry = {
                        "path": rel_path,
                        "text": text,
                    }
                except UnicodeDecodeError:
                    file_entry = {
                        "path": rel_path,
                        "blob": base64.b64encode(
                            content
                        ).decode(),
                    }
                self._client.invoke(
                    "writeFiles",
                    {"content": [file_entry]},
                )
                results.append(
                    FileUploadResponse(path=path, error=None)
                )
            except Exception:
                results.append(
                    FileUploadResponse(
                        path=path, error="permission_denied"
                    )
                )
        return results

    def download_files(
        self, paths: list[str]
    ) -> list[FileDownloadResponse]:
        """Download files using the native ``readFiles`` API."""
        if not paths:
            return []
        self._ensure_session()
        results: list[FileDownloadResponse] = []
        for path in paths:
            try:
                rel_path = path.lstrip("/") or path
                response = self._client.invoke(
                    "readFiles", {"paths": [rel_path]}
                )
                content: bytes | None = None
                found = False
                for event in response.get("stream", []):
                    result = event.get("result", {})
                    for item in result.get("content", []):
                        if item.get("type") == "resource":
                            res = item.get("resource", {})
                            if "text" in res:
                                content = res["text"].encode(
                                    "utf-8"
                                )
                                found = True
                            elif "blob" in res:
                                content = base64.b64decode(
                                    res["blob"]
                                )
                                found = True
                if found:
                    results.append(
                        FileDownloadResponse(
                            path=path,
                            content=content,
                            error=None,
                        )
                    )
                else:
                    results.append(
                        FileDownloadResponse(
                            path=path,
                            content=None,
                            error="file_not_found",
                        )
                    )
            except Exception:
                results.append(
                    FileDownloadResponse(
                        path=path,
                        content=None,
                        error="file_not_found",
                    )
                )
        return results


__all__ = [
    "AgentCoreCodeInterpreterSandbox",
    "_extract_python_from_command",
]
