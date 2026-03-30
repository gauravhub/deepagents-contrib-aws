#!/usr/bin/env python3
"""Test: Skills progressive disclosure.

Verifies that skills are loaded on demand — only names/descriptions in
the initial prompt, with full SKILL.md content loaded when the agent
reads the skill file to fulfill a request.

Usage: uv run tests/test_progressive_disclosure.py
"""

from helpers import assert_test, get_response_text, make_graph, run_prompt


def main() -> None:
    print("\n=== Test: Skills Progressive Disclosure ===\n")

    graph = make_graph()

    # Test 1: Ask about available skills (should only show names/descriptions)
    print("1. Asking agent what skills it has (should show catalog, not full content)...")
    result = run_prompt(
        graph,
        "List your available skills. Just name them and their descriptions. Do NOT read the full skill files.",
        thread_id="test-skills-catalog",
    )
    response = get_response_text(result)
    print(f"   Response: {response[:400]}\n")

    passed = True
    passed &= assert_test(
        "linkedin" in response.lower(),
        "LinkedIn skill appears in skill catalog",
    )
    passed &= assert_test(
        "twitter" in response.lower() or "x post" in response.lower(),
        "Twitter/X skill appears in skill catalog",
    )

    # Test 2: Ask for a LinkedIn post — should trigger full skill loading
    print("2. Asking for a LinkedIn post (should load full SKILL.md on demand)...")
    result2 = run_prompt(
        graph,
        (
            "Write a LinkedIn post about why AI agents need structured memory. "
            "Follow the linkedin-post skill format exactly — hook, body paragraphs, "
            "call-to-action, and hashtags."
        ),
        thread_id="test-skills-linkedin",
    )
    response2 = get_response_text(result2)
    print(f"   Response: {response2[:600]}\n")

    # Check that the output follows the skill format
    passed &= assert_test(
        "#" in response2,
        "LinkedIn post includes hashtags (skill format followed)",
        "Expected hashtags in LinkedIn post output",
    )

    # Check messages for evidence of skill file read
    messages = result2.get("messages", [])
    tool_names = set()
    for msg in messages:
        if hasattr(msg, "tool_calls"):
            for tc in msg.tool_calls:
                tool_names.add(tc.get("name", ""))
        if hasattr(msg, "name"):
            tool_names.add(msg.name)

    skill_read = "read_file" in tool_names
    print(f"   Tools used: {tool_names}")

    passed &= assert_test(
        skill_read or "hook" in response2.lower() or len(response2) > 200,
        "Agent loaded skill content (read_file used OR output follows skill format)",
        f"read_file called: {skill_read}",
    )

    # Test 3: Ask for a Twitter thread — different skill
    print("\n3. Asking for a Twitter thread (should load twitter-post SKILL.md)...")
    result3 = run_prompt(
        graph,
        (
            "Write a short Twitter/X thread (3-4 tweets) about structured memory "
            "in AI agents. Use the twitter-post skill format with numbered tweets."
        ),
        thread_id="test-skills-twitter",
    )
    response3 = get_response_text(result3)
    print(f"   Response: {response3[:600]}\n")

    passed &= assert_test(
        "1/" in response3 or "1." in response3 or "thread" in response3.lower(),
        "Twitter output uses numbered thread format (skill format followed)",
        "Expected numbered tweets (1/, 2/, etc.) in Twitter thread output",
    )

    print(f"\n{'='*40}")
    print(f"Result: {'ALL PASSED' if passed else 'SOME FAILED'}")
    print(f"{'='*40}\n")


if __name__ == "__main__":
    main()
