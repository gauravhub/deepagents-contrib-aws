# Product Support Agent

A deep agent example that provides product support across three categories — consumer electronics, healthcare devices, and financial products — using the deepagents framework with AWS backends.

## Architecture

```
┌──────────────────────────────────────────────┐
│  Product Support Agent (deepagents)          │
│                                              │
│  CompositeBackend                            │
│  ├── default: AgentCore Code Interpreter     │
│  │   (Python + shell execution)              │
│  └── S3 routes:                              │
│      /memories/           → S3Backend        │
│      /skills/             → S3Backend        │
│      /conversation_history/ → S3Backend      │
│      /large_tool_results/ → S3Backend        │
└──────────────────────────────────────────────┘
```

## Prerequisites

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/)
- AWS credentials with permissions for:
  - Amazon S3 (read/write to your bucket)
  - Amazon Bedrock AgentCore Code Interpreter
- An S3 bucket for persistent storage

## Setup

```bash
cd examples/product_support_agent

# Configure environment
cp .env.example .env
# Edit .env with your S3 bucket, region, etc.

# Install dependencies (isolated venv)
uv sync

# Upload skills and memory to S3
uv run setup_backend.py
```

## Run

```bash
uv run langgraph dev
```

Then open LangGraph Studio at the URL shown in the terminal.

## Skills

The agent has 3 product support skills stored in S3:

| Skill | Directory | Covers |
|-------|-----------|--------|
| Electronics Support | `skills/electronics-support/SKILL.md` | TVs, laptops, smartphones, headphones — power, connectivity, display, battery, audio issues |
| Healthcare Products | `skills/healthcare-products/SKILL.md` | BP monitors, pulse oximeters, thermometers, fitness trackers — usage, calibration, error codes, safety |
| Finance Products | `skills/finance-products/SKILL.md` | Payment terminals, card readers, POS systems, banking apps — transactions, connectivity, security |

Each skill follows the [Anthropic Agent Skills](https://agentskills.io/specification) format: a directory named after the skill containing a `SKILL.md` file with YAML frontmatter (`name`, `description`) and markdown instructions.

## Example Conversations

**Electronics:**
> "My laptop won't turn on after I closed the lid yesterday"

**Healthcare:**
> "My blood pressure monitor shows error code E2"

**Finance:**
> "Our payment terminal keeps showing 'connection refused'"

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `S3_BACKEND_BUCKET` | Yes | S3 bucket for persistent storage |
| `S3_BACKEND_PREFIX` | No | Key prefix (e.g., `product-support/`) |
| `AWS_REGION` | Yes | AWS region for S3 and AgentCore |
| `AWS_DEFAULT_REGION` | No | AWS region fallback (if `AWS_REGION` not set) |
