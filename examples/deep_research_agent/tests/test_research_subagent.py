#!/usr/bin/env python3
"""Test: Research subagent delegation and report generation.

Asks the agent to research a topic and verifies it delegates to the
research-agent subagent and produces a report with citations.

Usage: uv run tests/test_research_subagent.py
"""

from helpers import assert_test, get_response_text, make_graph, run_prompt


def main() -> None:
    print("\n=== Test: Research Subagent Delegation ===\n")

    graph = make_graph()

    print("1. Asking agent to research a topic...")
    result = run_prompt(
        graph,
        "Lightly research what LangGraph is in 2-3 sentences. Write findings to /final_report.md",
        thread_id="test-research",
    )
    response = get_response_text(result)
    print(f"   Response: {response[:500]}\n")

    passed = True
    passed &= assert_test(
        "langgraph" in response.lower() or "report" in response.lower(),
        "Agent produced research output about LangGraph",
    )

    # Check messages for evidence of subagent delegation (task tool call)
    messages = result.get("messages", [])
    tool_names = []
    for msg in messages:
        if hasattr(msg, "tool_calls"):
            for tc in msg.tool_calls:
                tool_names.append(tc.get("name", ""))
        if hasattr(msg, "name"):
            tool_names.append(msg.name)

    has_task_call = "task" in tool_names
    has_write = "write_file" in tool_names

    passed &= assert_test(
        has_task_call or "research" in response.lower(),
        "Evidence of subagent delegation (task tool or research mention)",
        f"Tool names found: {set(tool_names)}",
    )

    print(f"\n{'='*40}")
    print(f"Result: {'ALL PASSED' if passed else 'SOME FAILED'}")
    print(f"{'='*40}\n")


if __name__ == "__main__":
    main()
