#!/usr/bin/env python3
"""Test: Large tool result eviction to S3.

The FilesystemMiddleware evicts tool results > 20k tokens (~80k chars) to
/large_tool_results/. This test generates a very large output via the
AgentCore sandbox to trigger eviction, then checks S3 for the offloaded file.

Usage: uv run tests/test_large_tool_results.py
"""

from helpers import assert_test, get_response_text, list_s3_files, make_graph, run_prompt


def main() -> None:
    print("\n=== Test: Large Tool Result Eviction to S3 ===\n")

    graph = make_graph()

    # Generate output > 80k chars to trigger eviction (20k tokens * 4 chars/token)
    # Ask the sandbox to generate a massive string
    print("1. Generating large output via sandbox (>80k chars to trigger eviction)...")
    result = run_prompt(
        graph,
        (
            "Run this Python code and return the full output:\n"
            "```python\n"
            "# Generate a large output to test eviction\n"
            "import json\n"
            "data = []\n"
            "for i in range(2000):\n"
            "    data.append({\n"
            "        'id': i,\n"
            "        'name': f'Item {i}',\n"
            "        'description': f'This is a detailed description for item number {i}. ' * 5,\n"
            "        'category': f'Category-{i % 20}',\n"
            "        'tags': [f'tag-{j}' for j in range(10)],\n"
            "        'metadata': {f'key_{k}': f'value_{k}_{i}' for k in range(5)}\n"
            "    })\n"
            "output = json.dumps(data, indent=2)\n"
            "print(f'Generated {len(output)} characters of JSON')\n"
            "print(output)\n"
            "```"
        ),
        thread_id="test-large-tool",
    )
    response = get_response_text(result)
    print(f"   Response (first 300 chars): {response[:300]}\n")

    # Check if the response mentions the file was offloaded
    was_evicted = (
        "large_tool_results" in response.lower()
        or "offloaded" in response.lower()
        or "saved to" in response.lower()
    )

    # Also check the messages for truncation markers
    messages = result.get("messages", [])
    has_eviction_marker = False
    for msg in messages:
        content = str(getattr(msg, "content", ""))
        if "large_tool_results" in content or "offloaded" in content.lower():
            has_eviction_marker = True
            break

    print("2. Checking S3 for large_tool_results/ files...")
    files = list_s3_files("large_tool_results/")
    print(f"   Found {len(files)} file(s)")
    for f in files:
        print(f"     - {f}")
    print()

    passed = True
    passed &= assert_test(
        len(files) > 0 or has_eviction_marker or was_evicted,
        "Large tool result was evicted (S3 file exists OR eviction marker in messages)",
        f"S3 files: {len(files)}, eviction marker: {has_eviction_marker}, response mention: {was_evicted}",
    )

    if len(files) > 0:
        passed &= assert_test(
            any("large_tool_results" in f for f in files),
            "Evicted file is under large_tool_results/ prefix",
        )

    # Also verify the agent can still work after eviction
    print("3. Verifying agent still works after large result...")
    result2 = run_prompt(
        graph,
        "What is 2 + 2? Answer with just the number.",
        thread_id="test-large-tool-followup",
    )
    response2 = get_response_text(result2)
    print(f"   Response: {response2[:100]}\n")

    passed &= assert_test(
        "4" in response2,
        "Agent still functional after large result eviction",
    )

    print(f"\n{'='*40}")
    print(f"Result: {'ALL PASSED' if passed else 'SOME FAILED'}")
    print(f"{'='*40}\n")


if __name__ == "__main__":
    main()
