#!/usr/bin/env python3
"""Test: Episodic memory persistence to S3.

Asks the agent to research a topic and save a dated session log to
/memories/episodic/. Verifies the file lands in S3 with a date-prefixed name.

Usage: uv run tests/test_episodic_memory.py
"""

from helpers import (
    assert_test,
    get_response_text,
    list_s3_files,
    make_graph,
    read_s3_file,
    run_prompt,
)


def main() -> None:
    print("\n=== Test: Episodic Memory Persistence ===\n")

    graph = make_graph()

    # Ask the agent to do research and save an episodic session log
    print("1. Asking agent to research and save an episodic session log...")
    result = run_prompt(
        graph,
        (
            "Research what Amazon S3 is in one sentence, then save an episodic memory "
            "session log to /memories/episodic/ with today's date in the filename "
            "(e.g., 2026-03-30_s3_research.md). The log should include: topic researched, "
            "date, key finding, and source."
        ),
        thread_id="test-episodic-mem",
    )
    response = get_response_text(result)
    print(f"   Response: {response[:400]}\n")

    # Check S3 for episodic memory files
    print("2. Checking S3 for episodic memory files...")
    files = list_s3_files("memories/episodic/")
    print(f"   Found {len(files)} file(s):")
    for f in files:
        print(f"     - {f}")
    print()

    passed = True
    passed &= assert_test(
        len(files) > 0,
        "Episodic memory file exists in S3",
        "No files found under memories/episodic/",
    )

    if files:
        # Check that the file is under episodic prefix (not general memories/)
        passed &= assert_test(
            any("episodic" in f for f in files),
            "File is under memories/episodic/ prefix (longest-prefix routing works)",
        )

        # Check for date pattern in filename
        import re
        has_date = any(re.search(r"\d{4}-\d{2}-\d{2}", f) for f in files)
        passed &= assert_test(
            has_date,
            "Filename contains date prefix (YYYY-MM-DD pattern)",
            f"Files: {files}",
        )

        # Read the content
        print("3. Reading episodic memory content from S3...")
        content = read_s3_file(files[-1])
        print(f"   Content (first 300 chars): {content[:300]}\n")

        passed &= assert_test(
            len(content) > 20,
            "Episodic memory has meaningful content",
            f"Content length: {len(content)}",
        )

    print(f"\n{'='*40}")
    print(f"Result: {'ALL PASSED' if passed else 'SOME FAILED'}")
    print(f"{'='*40}\n")


if __name__ == "__main__":
    main()
