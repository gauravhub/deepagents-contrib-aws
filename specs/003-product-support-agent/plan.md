# Implementation Plan: Product Support Agent Example

**Branch**: `feature/product-support-agent` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)

## Summary

Build a self-contained example in `examples/product_support_agent/` demonstrating a deepagents product support agent using `CompositeBackend` — `AgentCoreCodeInterpreterSandbox` for execution, `S3Backend` for persistent storage of memories, skills, conversation history, and large tool results. Includes 3 domain-specific skills (electronics, healthcare, finance) and a setup script for S3 bootstrapping.

## Technical Context

**Language/Version**: Python >=3.11
**Dependencies**: deepagents>=0.4.0, deepagents-contrib-aws>=0.2.0, python-dotenv, langgraph
**Project Type**: Example application (standalone, not a library)
**Testing**: Manual validation via LangGraph Studio (no automated tests — this is an example)

## Architecture

```
graph.py (entrypoint)
    │
    ├── load .env
    ├── build CompositeBackend
    │     ├── default: AgentCoreCodeInterpreterSandbox
    │     └── routes:
    │           /memories/           → S3Backend
    │           /skills/             → S3Backend
    │           /conversation_history/ → S3Backend
    │           /large_tool_results/ → S3Backend
    │
    └── create_deep_agent(backend=composite, memory=[...], skills=[...])
         → export compiled graph for LangGraph Studio

setup_backend.py (bootstrap)
    │
    ├── read local skills/*.md and memory/AGENTS.md
    └── upload to S3 via S3Backend (idempotent)
```

## Project Structure

```text
examples/product_support_agent/
├── pyproject.toml              # isolated deps
├── .env.example                # S3_BACKEND_BUCKET, S3_BACKEND_PREFIX, AGENTCORE_REGION
├── README.md                   # setup + run instructions
├── graph.py                    # LangGraph entrypoint
├── setup_backend.py            # S3 bootstrap script
├── skills/
│   ├── electronics-support.md  # diagnostic decision tree
│   ├── healthcare-products.md  # usage + calibration + safety
│   └── finance-products.md     # transaction troubleshooting
└── memory/
    └── AGENTS.md               # agent personality + behavior
```

## Key Design Decisions

1. **Fully isolated**: Own `pyproject.toml`, own `.venv`. No workspace, no parent coupling. Pulls `deepagents-contrib-aws>=0.2.0` from PyPI.
2. **CompositeBackend pattern**: Mirrors the proven pattern from the reference `graph.py` — default backend handles execution, S3 routes handle persistence.
3. **Idempotent setup**: `setup_backend.py` checks if files exist before uploading, so it's safe to run multiple times.
4. **Skill format**: Each skill is a structured markdown file following deepagents conventions — the agent reads and follows the instructions.
5. **LangGraph Studio compatible**: `graph.py` exports the compiled graph for `uv run langgraph dev`.
