#!/usr/bin/env python3
"""Clean all memory files from S3 (semantic, episodic, procedural).

Deletes everything under memories/semantic/, memories/episodic/,
and memories/procedural/ including both user/ and shared/ scopes.

Usage: uv run tests/clean_memories.py
       uv run tests/clean_memories.py --category semantic
       uv run tests/clean_memories.py --scope user --user-id alice
"""

from __future__ import annotations

import argparse

from helpers import delete_s3_prefix, list_s3_files

CATEGORIES = ["semantic", "episodic", "procedural"]


def clean(category: str, scope: str | None, user_id: str | None) -> int:
    """Delete memory files for a category, optionally filtered by scope."""
    if scope == "user" and user_id:
        prefix = f"memories/{category}/user/{user_id}/"
    elif scope:
        prefix = f"memories/{category}/{scope}/"
    else:
        prefix = f"memories/{category}/"

    files = list_s3_files(prefix)
    if not files:
        print(f"  {category}: no files")
        return 0

    deleted = delete_s3_prefix(prefix)
    print(f"  {category}: deleted {deleted} file(s)")
    for f in files:
        print(f"    - {f}")
    return deleted


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean memory files from S3"
    )
    parser.add_argument(
        "--category", "-c",
        choices=CATEGORIES,
        help="Only clean this category (default: all)",
    )
    parser.add_argument(
        "--scope", "-s",
        choices=["user", "shared"],
        help="Only clean this scope (default: both)",
    )
    parser.add_argument(
        "--user-id", "-u",
        help="Only clean this user's private files (requires --scope user)",
    )
    args = parser.parse_args()

    if args.user_id and args.scope != "user":
        parser.error("--user-id requires --scope user")

    categories = [args.category] if args.category else CATEGORIES

    print("\n=== Cleaning Memory Files ===\n")

    total = 0
    for cat in categories:
        total += clean(cat, args.scope, args.user_id)

    print(f"\nTotal: {total} file(s) deleted.")
    print("=" * 40 + "\n")


if __name__ == "__main__":
    main()
