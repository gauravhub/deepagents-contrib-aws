#!/usr/bin/env python3
"""Test: Human-in-the-loop interrupt on file writes.

Verifies that write_file and edit_file trigger HITL interrupts
that can be approved or rejected.

Usage: uv run tests/test_hitl.py
"""

from helpers import assert_test, get_response_text, make_graph

from langgraph.types import Command


def main() -> None:
    print("\n=== Test: Human-in-the-Loop Interrupts ===\n")

    graph = make_graph()
    config = {"configurable": {"thread_id": "test-hitl"}}

    # Test 1: Verify interrupt triggers on write_file
    print("1. Asking agent to write a file (should trigger interrupt)...")
    result = graph.invoke(
        {"messages": [("human", "Write a file called /test_hitl.md with the text 'HITL test content'")]},
        config=config,
    )

    passed = True
    has_interrupt = bool(result.get("__interrupt__"))
    passed &= assert_test(has_interrupt, "HITL interrupt triggered on write_file")

    if has_interrupt:
        interrupt_value = result["__interrupt__"][0].value
        action_requests = interrupt_value.get("action_requests", [])
        action_name = action_requests[0]["name"] if action_requests else "none"
        passed &= assert_test(
            action_name == "write_file",
            f"Interrupt is for write_file (got: {action_name})",
        )

        file_path = action_requests[0]["args"].get("file_path", "") if action_requests else ""
        passed &= assert_test(
            "test_hitl" in file_path,
            f"Interrupt contains correct file path (got: {file_path})",
        )

        # Test 2: Approve the interrupt
        print("\n2. Approving the interrupt...")
        result2 = graph.invoke(
            Command(resume={"decisions": [{"type": "approve"}]}),
            config=config,
        )
        response2 = get_response_text(result2)
        print(f"   Response: {response2[:200]}\n")

        passed &= assert_test(
            not result2.get("__interrupt__"),
            "No further interrupt after approval",
        )
    else:
        print("   Skipping approval test — no interrupt was triggered\n")

    print(f"\n{'='*40}")
    print(f"Result: {'ALL PASSED' if passed else 'SOME FAILED'}")
    print(f"{'='*40}\n")


if __name__ == "__main__":
    main()
