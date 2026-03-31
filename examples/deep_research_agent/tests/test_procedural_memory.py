#!/usr/bin/env python3
"""Test: Procedural memory with user/shared scoping.

Alice saves a private workflow preference and a shared team standard.
Bob can see the shared standard but NOT Alice's private workflow.

Usage: uv run tests/test_procedural_memory.py
"""

from helpers import (
    assert_test,
    delete_s3_prefix,
    get_response_text,
    list_s3_files,
    make_graph,
    run_prompt,
)


def main() -> None:
    print("\n=== Test: Procedural Memory — User/Shared Scoping ===\n")

    # Clean up old procedural memory files
    print("0. Cleaning up old procedural memory files in S3...")
    deleted = delete_s3_prefix("memories/procedural/")
    print(f"   Deleted {deleted} old file(s).\n")

    graph = make_graph()

    # --- Alice saves private workflow + shared standard ---
    print("1. Alice: saving private workflow and shared standard...")
    result = run_prompt(
        graph,
        (
            "Save these two things:\n"
            "1. To /memories/procedural/user/my_workflow.md: "
            "'Alice always runs tests before committing code'\n"
            "2. To /memories/procedural/shared/coding_standards.md: "
            "'Team standard: Use numbered lists for action items "
            "and always include docstrings'"
        ),
        thread_id="test-procedural-alice",
        user_id="alice",
    )
    response = get_response_text(result)
    print(f"   Response: {response[:300]}\n")

    # Check S3 — Alice's user prefix
    print("2. Checking S3 for Alice's private procedural files...")
    alice_files = list_s3_files("memories/procedural/user/alice/")
    print(f"   Found {len(alice_files)} file(s): {alice_files}\n")

    # Check S3 — shared prefix
    print("3. Checking S3 for shared procedural files...")
    shared_files = list_s3_files("memories/procedural/shared/")
    print(f"   Found {len(shared_files)} file(s): {shared_files}\n")

    passed = True
    passed &= assert_test(
        len(alice_files) > 0,
        "Alice's private procedural file exists in S3",
        "No files under memories/procedural/user/alice/",
    )
    passed &= assert_test(
        len(shared_files) > 0,
        "Shared procedural file exists in S3",
        "No files under memories/procedural/shared/",
    )

    # --- Bob tries to read both scopes ---
    print("\n4. Bob: listing files in user/ and shared/ scopes...")
    result_bob = run_prompt(
        graph,
        (
            "List all files in /memories/procedural/user/ and "
            "/memories/procedural/shared/ and tell me what you find."
        ),
        thread_id="test-procedural-bob",
        user_id="bob",
    )
    response_bob = get_response_text(result_bob)
    print(f"   Response: {response_bob[:400]}\n")

    # Bob should NOT see Alice's private files
    bob_user_files = list_s3_files("memories/procedural/user/bob/")
    print(f"5. Bob's private files: {bob_user_files}")

    passed &= assert_test(
        len(bob_user_files) == 0,
        "Bob has no private procedural files (isolation works)",
        f"Unexpected files: {bob_user_files}",
    )

    passed &= assert_test(
        len(shared_files) > 0,
        "Bob can access shared procedural files",
    )

    print(f"\n{'='*50}")
    print(f"Result: {'ALL PASSED' if passed else 'SOME FAILED'}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
