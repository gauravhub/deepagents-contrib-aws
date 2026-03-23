"""AWS contributions for Deep Agents."""

from deepagents_contrib_aws.s3_backend import S3Backend

try:
    from deepagents_contrib_aws.agentcore_sandbox import (
        AgentCoreCodeInterpreterSandbox,
    )
except ImportError:

    class AgentCoreCodeInterpreterSandbox:  # type: ignore[no-redef]
        """Stub raised when bedrock-agentcore is not installed."""

        def __init__(self, *args, **kwargs):
            raise ImportError(
                "bedrock-agentcore is required for "
                "AgentCoreCodeInterpreterSandbox. "
                "Install with: "
                "pip install deepagents-contrib-aws[agentcore]"
            )


__all__ = ["S3Backend", "AgentCoreCodeInterpreterSandbox"]
__version__ = "0.2.0"
