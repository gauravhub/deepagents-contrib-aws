#!/usr/bin/env python3
"""Test: Procedural memory persistence to S3.

Saves a formatting rule to /memories/procedural/ and verifies it lands
in the correct S3 prefix.

Usage: uv run tests/test_procedural_memory.py
"""

from helpers import assert_test, get_response_text, list_s3_files, make_graph, run_prompt


def main() -> None:
    print("\n=== Test: Procedural Memory Persistence ===\n")

    graph = make_graph()

    print("1. Saving formatting rule to procedural memory...")
    result = run_prompt(
        graph,
        "Save this rule to procedural memory: Always use numbered lists instead of bullet points for action items.",
        thread_id="test-procedural-mem",
    )
    response = get_response_text(result)
    print(f"   Response: {response[:200]}\n")

    print("2. Checking S3 for procedural memory files...")
    files = list_s3_files("memories/procedural/")
    print(f"   Found {len(files)} file(s): {files}\n")

    passed = True
    passed &= assert_test(len(files) > 0, "Procedural memory file exists in S3")
    passed &= assert_test(
        any("procedural" in f for f in files),
        "File is under memories/procedural/ prefix (not memories/)",
    )

    print(f"\n{'='*40}")
    print(f"Result: {'ALL PASSED' if passed else 'SOME FAILED'}")
    print(f"{'='*40}\n")


if __name__ == "__main__":
    main()
