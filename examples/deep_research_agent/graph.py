#!/usr/bin/env python3
"""LangGraph Studio entrypoint for the Deep Research Agent.

Exports a compiled deep agent graph that uses:
- AgentCoreCodeInterpreterSandbox for code execution (default)
- S3Backend for persistent storage (memories, skills, history)
- Research subagent for delegated web research via Tavily
- Structured long-term memory (semantic, episodic, procedural)
- Human-in-the-loop on file writes and edits

Run with: uv run langgraph dev
"""

from __future__ import annotations

import os
import sys
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from deepagents import create_deep_agent
from deepagents.backends.composite import CompositeBackend
from deepagents_contrib_aws import (
    AgentCoreCodeInterpreterSandbox,
    S3Backend,
)
from langchain_aws import ChatBedrockConverse
from langchain_core.tools import tool
from tavily import TavilyClient

# --- System Prompt ---

SYSTEM_PROMPT = """\
You are an expert research assistant. You help users research topics, \
synthesize findings, and produce polished reports and content.

## Structured Long-Term Memory

Your memory is organized into three types, each stored persistently in S3:

- `/memories/semantic/` — Facts & knowledge: user preferences, topic summaries, \
project context. Example files: `user_preferences.md`, `project_context.md`
- `/memories/episodic/` — Past experiences: dated research session logs, interaction \
summaries. Example files: `2025-03-30_ai_agents_research.md`, `session_log.md`
- `/memories/procedural/` — Instructions & rules: report formatting, citation \
standards, learned workflows. Example files: `report_format.md`, `coding_standards.md`

When asked to remember something, categorize it and save to the appropriate \
memory type. When starting a new research task, check all three memory paths \
for relevant prior knowledge.

Regular files (not in `/memories/`) are ephemeral scratch space.\
"""

# --- Tools ---

tavily_client = TavilyClient()


@tool(parse_docstring=True)
def tavily_search(query: str) -> str:
    """Search the web for information on a given query.

    Args:
        query: Search query to execute
    """
    search_results = tavily_client.search(query, max_results=3, topic="general")

    result_texts = []
    for result in search_results.get("results", []):
        url = result["url"]
        title = result["title"]
        content = result.get("content", "No content available")
        result_text = f"## {title}\n**URL:** {url}\n\n{content}\n\n---\n"
        result_texts.append(result_text)

    return f"Found {len(result_texts)} result(s) for '{query}':\n\n{''.join(result_texts)}"


# --- Research Subagent ---

current_date = datetime.now().strftime("%Y-%m-%d")

RESEARCHER_INSTRUCTIONS = f"""You are a research assistant conducting research. Today's date is {current_date}.

<Task>
Use tools to gather information about the research topic.
</Task>

<Hard Limits>
- Simple queries: Use 2-3 search tool calls maximum
- Complex queries: Use up to 5 search tool calls maximum
- After each search, reflect on findings before the next search
</Hard Limits>

<Output Format>
Structure your findings with:
- Clear headings
- Inline citations [1], [2], [3]
- Sources section at the end
</Output Format>
"""

research_subagent = {
    "name": "research-agent",
    "description": "Delegate research tasks. Give one topic at a time.",
    "system_prompt": RESEARCHER_INSTRUCTIONS,
    "tools": [tavily_search],
}


# --- Backend ---


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
        "/memories/semantic/": _s3("memories/semantic"),
        "/memories/episodic/": _s3("memories/episodic"),
        "/memories/procedural/": _s3("memories/procedural"),
        "/memories/": _s3("memories"),
        "/skills/": _s3("skills"),
        "/conversation_history/": _s3("conversation_history"),
        "/large_tool_results/": _s3("large_tool_results"),
    }

    return CompositeBackend(default=sandbox, routes=routes)


# --- Agent ---

backend = _build_backend()

region = (
    os.environ.get("AWS_REGION")
    or os.environ.get("AWS_DEFAULT_REGION")
)

graph = create_deep_agent(
    model=ChatBedrockConverse(
        model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name=region,
    ),
    tools=[tavily_search],
    system_prompt=SYSTEM_PROMPT,
    memory=["/memories/AGENTS.md"],
    skills=["/skills/"],
    subagents=[research_subagent],
    backend=backend,
    interrupt_on={
        "write_file": True,
        "edit_file": True,
    },
)
