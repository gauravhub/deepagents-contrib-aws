#!/usr/bin/env python3
"""Test: Semantic memory persistence to S3.

Saves a user preference to /memories/semantic/ and verifies it lands
in the correct S3 prefix.

Usage: uv run tests/test_semantic_memory.py
"""

from helpers import assert_test, get_response_text, list_s3_files, make_graph, run_prompt


def main() -> None:
    print("\n=== Test: Semantic Memory Persistence ===\n")

    graph = make_graph()

    # Save a fact to semantic memory
    print("1. Saving user preference to semantic memory...")
    result = run_prompt(
        graph,
        "Save this fact to semantic memory: My favorite programming language is Python and I work at AWS.",
        thread_id="test-semantic-mem",
    )
    response = get_response_text(result)
    print(f"   Response: {response[:200]}\n")

    # Check S3
    print("2. Checking S3 for semantic memory files...")
    files = list_s3_files("memories/semantic/")
    print(f"   Found {len(files)} file(s): {files}\n")

    passed = True
    passed &= assert_test(len(files) > 0, "Semantic memory file exists in S3")
    passed &= assert_test(
        any("semantic" in f for f in files),
        "File is under memories/semantic/ prefix",
    )

    # Verify content via recall in new thread
    print("\n3. Recalling from semantic memory in new thread...")
    result2 = run_prompt(
        graph,
        "Check /memories/semantic/ and tell me what facts you have stored about me.",
        thread_id="test-semantic-recall",
    )
    response2 = get_response_text(result2)
    print(f"   Response: {response2[:300]}\n")

    passed &= assert_test(
        "python" in response2.lower() or "aws" in response2.lower(),
        "Recalled stored semantic fact in new thread",
        "Expected mention of Python or AWS in recall response",
    )

    print(f"\n{'='*40}")
    print(f"Result: {'ALL PASSED' if passed else 'SOME FAILED'}")
    print(f"{'='*40}\n")


if __name__ == "__main__":
    main()
