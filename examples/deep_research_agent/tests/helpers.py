"""Shared helpers for deep research agent integration tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add parent directory so we can import graph module
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

from deepagents import create_deep_agent
from langchain_aws import ChatBedrockConverse
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from graph import (
    SYSTEM_PROMPT,
    backend,
    research_subagent,
    tavily_search,
)


def get_region() -> str:
    return os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"


def make_graph(checkpointer=None, interrupt_on=None):
    """Build a test graph with optional checkpointer and HITL config."""
    if checkpointer is None:
        checkpointer = MemorySaver()
    if interrupt_on is None:
        interrupt_on = {"write_file": True, "edit_file": True}

    return create_deep_agent(
        model=ChatBedrockConverse(
            model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
            region_name=get_region(),
        ),
        tools=[tavily_search],
        system_prompt=SYSTEM_PROMPT,
        memory=["/memories/AGENTS.md"],
        skills=["/skills/"],
        subagents=[research_subagent],
        backend=backend,
        interrupt_on=interrupt_on,
        checkpointer=checkpointer,
    )


def run_prompt(graph, prompt: str, thread_id: str, max_iterations: int = 20) -> dict:
    """Run a prompt, auto-approving HITL interrupts. Returns full result dict."""
    config = {"configurable": {"thread_id": thread_id}}

    result = graph.invoke(
        {"messages": [("human", prompt)]},
        config=config,
    )

    iterations = 0
    while result.get("__interrupt__") and iterations < max_iterations:
        iterations += 1
        interrupt_value = result["__interrupt__"][0].value
        action_requests = interrupt_value.get("action_requests", [])
        print(f"  [HITL] Auto-approving {len(action_requests)} action(s)...")
        for action in action_requests:
            print(f"    - {action['name']}: {action['args'].get('file_path', 'N/A')}")

        result = graph.invoke(
            Command(resume={"decisions": [{"type": "approve"} for _ in action_requests]}),
            config=config,
        )

    return result


def get_response_text(result: dict) -> str:
    """Extract text from the last message in a result."""
    last_msg = result["messages"][-1]
    return last_msg.content if isinstance(last_msg.content, str) else str(last_msg.content)


def list_s3_files(prefix_suffix: str = "") -> list[str]:
    """List files in S3 under the configured prefix + suffix."""
    import boto3

    bucket = os.environ["S3_BACKEND_BUCKET"]
    base_prefix = os.environ.get("S3_BACKEND_PREFIX", "").strip("/")
    if base_prefix:
        base_prefix += "/"
    full_prefix = f"{base_prefix}{prefix_suffix}"

    s3 = boto3.client("s3", region_name=get_region())
    response = s3.list_objects_v2(Bucket=bucket, Prefix=full_prefix)
    return [obj["Key"] for obj in response.get("Contents", [])]


def read_s3_file(key: str) -> str:
    """Read a file from S3 by full key."""
    import boto3

    bucket = os.environ["S3_BACKEND_BUCKET"]
    s3 = boto3.client("s3", region_name=get_region())
    obj = s3.get_object(Bucket=bucket, Key=key)
    return obj["Body"].read().decode("utf-8")


def print_pass(test_name: str):
    print(f"  PASS  {test_name}")


def print_fail(test_name: str, reason: str):
    print(f"  FAIL  {test_name}: {reason}")


def assert_test(condition: bool, test_name: str, fail_reason: str = ""):
    if condition:
        print_pass(test_name)
    else:
        print_fail(test_name, fail_reason)
    return condition
