#!/usr/bin/env python3
"""Test: AgentCore Code Interpreter sandbox execution.

Asks the agent to run Python code and verifies the result comes from
the AgentCore sandbox.

Usage: uv run tests/test_sandbox.py
"""

from helpers import assert_test, get_response_text, make_graph, run_prompt


def main() -> None:
    print("\n=== Test: AgentCore Sandbox Code Execution ===\n")

    graph = make_graph()

    print("1. Asking agent to calculate fibonacci numbers...")
    result = run_prompt(
        graph,
        "Calculate the first 10 fibonacci numbers using Python code execution. Show the code you ran.",
        thread_id="test-sandbox",
    )
    response = get_response_text(result)
    print(f"   Response: {response[:500]}\n")

    passed = True
    passed &= assert_test(
        "55" in response,
        "Correct fibonacci result (55 is the 10th fibonacci number)",
        "Expected '55' in response",
    )

    print("2. Asking agent to run a more complex computation...")
    result2 = run_prompt(
        graph,
        "Use Python code to calculate the sum of squares from 1 to 100. Just give me the number.",
        thread_id="test-sandbox-2",
    )
    response2 = get_response_text(result2)
    print(f"   Response: {response2[:300]}\n")

    passed &= assert_test(
        "338350" in response2,
        "Correct sum of squares result (338350)",
        f"Expected '338350' in response",
    )

    print(f"\n{'='*40}")
    print(f"Result: {'ALL PASSED' if passed else 'SOME FAILED'}")
    print(f"{'='*40}\n")


if __name__ == "__main__":
    main()
