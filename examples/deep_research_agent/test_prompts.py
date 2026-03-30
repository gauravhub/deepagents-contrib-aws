#!/usr/bin/env python3
"""Test the deep research agent with various prompts, auto-approving HITL interrupts.

Usage: uv run test_prompts.py
"""

from __future__ import annotations

import sys

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from graph import backend, tavily_search, research_subagent, SYSTEM_PROMPT

from deepagents import create_deep_agent
from langchain_aws import ChatBedrockConverse
import os

# Rebuild graph with a checkpointer so HITL resume works
checkpointer = MemorySaver()
region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")

graph = create_deep_agent(
    model=ChatBedrockConverse(
        model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name=region,
    ),
    tools=[tavily_search],
    system_prompt=SYSTEM_PROMPT,
    memory=["/memories/AGENTS.md"],
    skills=["/skills/"],
    subagents=[research_subagent],
    backend=backend,
    interrupt_on={
        "write_file": True,
        "edit_file": True,
    },
    checkpointer=checkpointer,
)


def run_prompt(prompt: str, thread_id: str = "test", max_iterations: int = 20) -> str:
    """Run a prompt through the agent, auto-approving any HITL interrupts."""
    config = {"configurable": {"thread_id": thread_id}}

    result = graph.invoke(
        {"messages": [("human", prompt)]},
        config=config,
    )

    # Handle HITL interrupts by auto-approving
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

    # Get final message
    last_msg = result["messages"][-1]
    content = last_msg.content if isinstance(last_msg.content, str) else str(last_msg.content)
    return content


def main() -> None:
    prompts = [
        (
            "test-semantic",
            "Save this fact to semantic memory: I prefer concise reports with bullet points rather than long paragraphs. My name is Gaurav.",
        ),
        (
            "test-procedural",
            "Save this rule to procedural memory: always include a TL;DR section at the top of research reports.",
        ),
        (
            "test-research",
            "Lightly research what Amazon Bedrock AgentCore is in 2-3 sentences. Write the report to /final_report.md",
        ),
        (
            "test-recall",
            "What do you remember about me? Check all memory types: semantic, episodic, and procedural.",
        ),
        (
            "test-sandbox",
            "Calculate the first 15 fibonacci numbers using Python code execution.",
        ),
    ]

    for thread_id, prompt in prompts:
        print(f"\n{'='*60}")
        print(f"PROMPT [{thread_id}]: {prompt[:80]}...")
        print(f"{'='*60}")
        try:
            response = run_prompt(prompt, thread_id=thread_id)
            print(f"\nRESPONSE:\n{response[:1000]}")
            if len(response) > 1000:
                print(f"... [{len(response)} chars total]")
        except Exception as e:
            print(f"\nERROR: {e}")
        print()


if __name__ == "__main__":
    main()
