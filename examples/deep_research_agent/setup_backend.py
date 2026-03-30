#!/usr/bin/env python3
"""Upload skills and memory files to S3.

Reads local skills/*.md and memory/AGENTS.md files, then uploads
them to S3 at the paths expected by the agent's CompositeBackend.

Idempotent — skips files that already exist in S3.

Usage: uv run setup_backend.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from deepagents_contrib_aws import S3Backend

SCRIPT_DIR = Path(__file__).parent

FILES_TO_UPLOAD = [
    ("skills/linkedin-post/SKILL.md", "/skills/linkedin-post/SKILL.md"),
    ("skills/twitter-post/SKILL.md", "/skills/twitter-post/SKILL.md"),
    ("memory/AGENTS.md", "/memories/AGENTS.md"),
]


def main() -> None:
    bucket = os.environ.get("S3_BACKEND_BUCKET")
    if not bucket:
        print(
            "Error: S3_BACKEND_BUCKET is not set. "
            "Copy .env.example to .env and configure it.",
            file=sys.stderr,
        )
        sys.exit(1)

    base_prefix = (
        os.environ.get("S3_BACKEND_PREFIX", "").strip("/")
    )
    if base_prefix:
        base_prefix = base_prefix + "/"

    s3_region = (
        os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
    )

    uploaded = 0
    skipped = 0

    for local_rel, s3_path in FILES_TO_UPLOAD:
        local_file = SCRIPT_DIR / local_rel
        if not local_file.exists():
            print(f"  MISSING  {local_rel} (file not found)")
            continue

        # Determine S3 prefix for this path
        s3_dir = s3_path.rsplit("/", 1)[0]  # e.g., "/skills/linkedin-post"
        s3_name = s3_path.rsplit("/", 1)[1]  # e.g., "SKILL.md"
        prefix = f"{base_prefix}{s3_dir.strip('/')}"
        if prefix:
            prefix = prefix.rstrip("/") + "/"

        backend = S3Backend(
            bucket=bucket,
            prefix=prefix,
            region_name=s3_region,
        )

        # Check if file already exists
        content = backend.read(f"/{s3_name}")
        if not content.startswith("Error:"):
            print(f"  SKIP     {s3_path} (already exists)")
            skipped += 1
            continue

        # Upload
        file_content = local_file.read_text(encoding="utf-8")
        result = backend.write(f"/{s3_name}", file_content)
        if hasattr(result, "error") and result.error:
            print(f"  ERROR    {s3_path}: {result.error}")
        else:
            print(f"  UPLOAD   {s3_path}")
            uploaded += 1

    print(
        f"\nDone: {uploaded} uploaded, "
        f"{skipped} skipped (already exist)"
    )


if __name__ == "__main__":
    main()
