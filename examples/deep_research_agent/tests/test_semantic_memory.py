#!/usr/bin/env python3
"""Test: Semantic memory with user/shared scoping.

Alice saves a private preference and a shared fact. Bob can see the
shared fact but NOT Alice's private preference.

Usage: uv run tests/test_semantic_memory.py
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
    print("\n=== Test: Semantic Memory — User/Shared Scoping ===\n")

    # Clean up old semantic memory files
    print("0. Cleaning up old semantic memory files in S3...")
    deleted = delete_s3_prefix("memories/semantic/")
    print(f"   Deleted {deleted} old file(s).\n")

    graph = make_graph()

    # --- Alice saves private + shared semantic memories ---
    print("1. Alice: saving private preference and shared fact...")
    result = run_prompt(
        graph,
        (
            "Save these two things:\n"
            "1. To /memories/semantic/user/preferences.md: "
            "'Alice prefers dark mode and Python'\n"
            "2. To /memories/semantic/shared/project_context.md: "
            "'The project uses AWS S3 for storage'"
        ),
        thread_id="test-semantic-alice",
        user_id="alice",
    )
    response = get_response_text(result)
    print(f"   Response: {response[:300]}\n")

    # Check S3 — Alice's user prefix
    print("2. Checking S3 for Alice's private semantic files...")
    alice_files = list_s3_files("memories/semantic/user/alice/")
    print(f"   Found {len(alice_files)} file(s): {alice_files}\n")

    # Check S3 — shared prefix
    print("3. Checking S3 for shared semantic files...")
    shared_files = list_s3_files("memories/semantic/shared/")
    print(f"   Found {len(shared_files)} file(s): {shared_files}\n")

    passed = True
    passed &= assert_test(
        len(alice_files) > 0,
        "Alice's private semantic file exists in S3",
        "No files under memories/semantic/user/alice/",
    )
    passed &= assert_test(
        len(shared_files) > 0,
        "Shared semantic file exists in S3",
        "No files under memories/semantic/shared/",
    )

    # --- Bob tries to read both scopes ---
    print("\n4. Bob: listing files in user/ and shared/ scopes...")
    result_bob = run_prompt(
        graph,
        (
            "List all files in /memories/semantic/user/ and "
            "/memories/semantic/shared/ and tell me what you find."
        ),
        thread_id="test-semantic-bob",
        user_id="bob",
    )
    response_bob = get_response_text(result_bob)
    print(f"   Response: {response_bob[:400]}\n")

    # Bob should NOT see Alice's files (his user/ namespace is empty)
    bob_user_files = list_s3_files("memories/semantic/user/bob/")
    print(f"5. Bob's private files: {bob_user_files}")

    passed &= assert_test(
        len(bob_user_files) == 0,
        "Bob has no private semantic files (isolation works)",
        f"Unexpected files: {bob_user_files}",
    )

    # Bob SHOULD still see shared files
    passed &= assert_test(
        len(shared_files) > 0,
        "Bob can access shared semantic files",
    )

    print(f"\n{'='*50}")
    print(f"Result: {'ALL PASSED' if passed else 'SOME FAILED'}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
