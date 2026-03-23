#!/usr/bin/env python3
"""LangGraph Studio entrypoint for the Product Support Agent.

Exports a compiled deep agent graph that uses:
- AgentCoreCodeInterpreterSandbox for code execution (default)
- S3Backend for persistent storage (memories, skills, history)

Run with: uv run langgraph dev
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()

from deepagents import create_deep_agent
from deepagents.backends.composite import CompositeBackend
from deepagents_contrib_aws import (
    AgentCoreCodeInterpreterSandbox,
    S3Backend,
)

SYSTEM_PROMPT = """\
You are a product support assistant. You help users troubleshoot \
and get information about products across three categories:

- **Consumer Electronics** (TVs, laptops, smartphones, headphones)
- **Healthcare/Wellness Devices** (BP monitors, pulse oximeters, \
thermometers, fitness trackers)
- **Financial Products** (payment terminals, card readers, POS \
systems, banking apps)

Use your skills library for structured troubleshooting. Always \
ask clarifying questions before diagnosing. Follow the step-by-step \
instructions in each skill. If a question falls outside your \
skills, acknowledge that honestly and suggest contacting the \
manufacturer.

For healthcare products, always include safety disclaimers. \
For financial products, always remind users about security \
best practices.\
"""


def _build_backend():
    """Build CompositeBackend with AgentCore + S3 routing."""
    bucket = os.environ.get("S3_BACKEND_BUCKET")
    if not bucket:
        print(
            "Error: S3_BACKEND_BUCKET is not set. "
            "Copy .env.example to .env and configure it.",
            file=sys.stderr,
        )
        sys.exit(1)

    region = (
        os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
    )
    if not region:
        print(
            "Error: No region configured. Set AWS_REGION "
            "in .env.",
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

    def _s3(suffix: str) -> S3Backend:
        prefix = f"{base_prefix}{suffix}".strip("/")
        return S3Backend(
            bucket=bucket,
            prefix=prefix or "",
            region_name=s3_region,
        )

    sandbox = AgentCoreCodeInterpreterSandbox(
        region_name=region,
    )

    routes = {
        "/memories/": _s3("memories"),
        "/skills/": _s3("skills"),
        "/conversation_history/": _s3("conversation_history"),
        "/large_tool_results/": _s3("large_tool_results"),
    }

    return CompositeBackend(default=sandbox, routes=routes)


backend = _build_backend()

graph = create_deep_agent(
    backend=backend,
    memory=["/memories/AGENTS.md"],
    skills=["/skills/"],
    system_prompt=SYSTEM_PROMPT,
)
