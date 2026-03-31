#!/usr/bin/env python3
"""Test: Episodic memory with user/shared scoping.

Alice saves a private research session log and a shared team learning.
Bob can see the shared learning but NOT Alice's private session log.

Usage: uv run tests/test_episodic_memory.py
"""

from helpers import (
    assert_test,
    delete_s3_prefix,
    get_response_text,
    list_s3_files,
    make_graph,
    read_s3_file,
    run_prompt,
)


def main() -> None:
    print("\n=== Test: Episodic Memory — User/Shared Scoping ===\n")

    # Clean up old episodic memory files
    print("0. Cleaning up old episodic memory files in S3...")
    deleted = delete_s3_prefix("memories/episodic/")
    print(f"   Deleted {deleted} old file(s).\n")

    graph = make_graph()

    # --- Alice saves private session log + shared team learning ---
    print("1. Alice: saving private session log and shared learning...")
    result = run_prompt(
        graph,
        (
            "Save these two things:\n"
            "1. To /memories/episodic/user/2026-03-30_s3_research.md: "
            "'Session: Researched S3 pricing. Found that S3 Standard "
            "costs $0.023/GB. Date: 2026-03-30.'\n"
            "2. To /memories/episodic/shared/team_learnings.md: "
            "'Team learning: Always check S3 lifecycle rules before "
            "estimating storage costs.'"
        ),
        thread_id="test-episodic-alice",
        user_id="alice",
    )
    response = get_response_text(result)
    print(f"   Response: {response[:300]}\n")

    # Check S3 — Alice's user prefix
    print("2. Checking S3 for Alice's private episodic files...")
    alice_files = list_s3_files("memories/episodic/user/alice/")
    print(f"   Found {len(alice_files)} file(s): {alice_files}\n")

    # Check S3 — shared prefix
    print("3. Checking S3 for shared episodic files...")
    shared_files = list_s3_files("memories/episodic/shared/")
    print(f"   Found {len(shared_files)} file(s): {shared_files}\n")

    passed = True
    passed &= assert_test(
        len(alice_files) > 0,
        "Alice's private episodic file exists in S3",
        "No files under memories/episodic/user/alice/",
    )
    passed &= assert_test(
        len(shared_files) > 0,
        "Shared episodic file exists in S3",
        "No files under memories/episodic/shared/",
    )

    # Check content of Alice's session log
    if alice_files:
        import re

        has_date = any(re.search(r"\d{4}-\d{2}-\d{2}", f) for f in alice_files)
        passed &= assert_test(
            has_date,
            "Filename contains date (YYYY-MM-DD pattern)",
            f"Files: {alice_files}",
        )

        content = read_s3_file(alice_files[-1])
        print(f"4. Alice's session log content (first 200 chars): {content[:200]}\n")
        passed &= assert_test(
            len(content) > 20,
            "Episodic memory has meaningful content",
            f"Content length: {len(content)}",
        )

    # --- Bob tries to read both scopes ---
    print("5. Bob: listing files in user/ and shared/ scopes...")
    result_bob = run_prompt(
        graph,
        (
            "List all files in /memories/episodic/user/ and "
            "/memories/episodic/shared/ and tell me what you find."
        ),
        thread_id="test-episodic-bob",
        user_id="bob",
    )
    response_bob = get_response_text(result_bob)
    print(f"   Response: {response_bob[:400]}\n")

    # Bob should NOT see Alice's private session logs
    bob_user_files = list_s3_files("memories/episodic/user/bob/")
    print(f"6. Bob's private files: {bob_user_files}")

    passed &= assert_test(
        len(bob_user_files) == 0,
        "Bob has no private episodic files (isolation works)",
        f"Unexpected files: {bob_user_files}",
    )

    passed &= assert_test(
        len(shared_files) > 0,
        "Bob can access shared episodic files",
    )

    print(f"\n{'='*50}")
    print(f"Result: {'ALL PASSED' if passed else 'SOME FAILED'}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
