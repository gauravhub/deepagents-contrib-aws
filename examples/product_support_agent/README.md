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

**Interactive CLI:**

```bash
uv run main.py
```

**LangGraph Studio** (visual UI):

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

## Testing S3 Storage Routes

The CompositeBackend routes different paths to S3. Here's how to verify each route is working:

### /skills/ and /memories/ (populated by setup)

These are populated when you run `uv run setup_backend.py`. Verify with:

```bash
aws s3 ls s3://<your-bucket>/<prefix>/skills/ --recursive
aws s3 ls s3://<your-bucket>/<prefix>/memories/
```

### /large_tool_results/ (auto-evicted large outputs)

When a tool output exceeds ~80K characters, the `FilesystemMiddleware` automatically saves it to S3 and replaces it with a truncated preview. Try this prompt:

> Use Python to print "x" * 100000

After the agent responds, check S3:

```bash
aws s3 ls s3://<your-bucket>/<prefix>/large_tool_results/
```

You should see a file named after the tool call ID containing the full output.

### /conversation_history/ (summarized conversations)

Summarization is configured to trigger at 10% of the context window (configurable via `SUMMARIZATION_TRIGGER` env var). After a few exchanges, the middleware evicts older messages to S3. To trigger it quickly, have a multi-turn conversation with tool use:

> 1. "Compare troubleshooting steps for a laptop that won't turn on vs one with a flickering screen"
> 2. "Now do the same comparison for blood pressure monitor errors E1 through E5"
> 3. "Write a Python script that creates a JSON summary of all the troubleshooting steps we discussed"
> 4. "Now compare payment terminal connection issues with card reader pairing problems"

After several exchanges, check S3:

```bash
aws s3 ls s3://<your-bucket>/<prefix>/conversation_history/
```

You should see a markdown file named after the thread ID containing the summarized conversation history.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key for Claude |
| `AWS_REGION` | Yes | AWS region for S3 and AgentCore |
| `S3_BACKEND_BUCKET` | Yes | S3 bucket for persistent storage |
| `S3_BACKEND_PREFIX` | No | Key prefix (e.g., `product-support/`) |
| `AWS_ACCESS_KEY_ID` | No* | AWS credentials (if not using IAM role/SSO) |
| `AWS_SECRET_ACCESS_KEY` | No* | AWS credentials |
| `AWS_SESSION_TOKEN` | No* | For temporary credentials (STS/SSO) |
| `LANGSMITH_API_KEY` | No | LangSmith API key for tracing |
| `LANGCHAIN_TRACING_V2` | No | Set to `true` to enable tracing |
| `LANGCHAIN_PROJECT` | No | LangSmith project name |

*AWS credentials are resolved via the standard boto3 chain — env vars, `~/.aws/credentials`, SSO, or IAM role.
