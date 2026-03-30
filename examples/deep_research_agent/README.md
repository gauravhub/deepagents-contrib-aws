# Deep Research Agent

A web research agent built with [Deep Agents](https://github.com/langchain-ai/deepagents) and AWS backends from `deepagents-contrib-aws`. It delegates research to a subagent, persists structured long-term memories to S3, generates social media content via skills, and supports human-in-the-loop approval for file operations.

## Architecture

```
User Request
    |
    v
+---------------------------------------------+
|  Deep Research Agent (Orchestrator)         |
|  - Plans with write_todos                   |
|  - Delegates to research-agent subagent     |
|  - Synthesizes reports                      |
|  - Loads skills on demand                   |
|  - Humn in the loop (HITL) on file writes   |
+----------+----------------------------------+
           |
     +-----+-----+
     | Subagent  |
     | research- |
     | agent     |
     | (tavily)  |
     +-----+-----+
           |
           v
+---------------------------------------------+
|  CompositeBackend                           |
|                                             |
|  Default: AgentCore Code Interpreter        |
|                                             |
|  S3 Routes:                                 |
|  /memories/semantic/    -> S3 (facts)       |
|  /memories/episodic/    -> S3 (experiences) |
|  /memories/procedural/  -> S3 (rules)       |
|  /memories/             -> S3 (AGENTS.md)   |
|  /skills/               -> S3 (SKILL.md)    |
|  /conversation_history/ -> S3 (evicted msgs)|
|  /large_tool_results/   -> S3 (big outputs) |
+---------------------------------------------+
```

## Structured Memory (Semantic / Episodic / Procedural)

Inspired by the [CoALA paper](https://arxiv.org/abs/2309.02427), memories are organized into three types, each stored at a separate S3 prefix:

| Memory Type | Path | What It Stores | Example Files |
|-------------|------|---------------|---------------|
| **Semantic** | `/memories/semantic/` | Facts & knowledge | `user_preferences.md`, `ai_agents_overview.md` |
| **Episodic** | `/memories/episodic/` | Past experiences | `2025-03-30_quantum_research.md`, `session_log.md` |
| **Procedural** | `/memories/procedural/` | Instructions & rules | `report_format.md`, `citation_style.md` |

The `CompositeBackend` uses **longest-prefix matching**, so `/memories/semantic/` routes to its own S3 prefix (`memories/semantic`), separate from the parent `/memories/` route.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- AWS credentials with access to:
  - **S3** (read/write to your bucket)
  - **Amazon Bedrock** (Claude model invocation)
  - **Bedrock AgentCore** (Code Interpreter)
- [Tavily API key](https://tavily.com) (free tier available)

## Quick Start

```bash
# 1. Navigate to the example
cd examples/deep_research_agent

# 2. Configure environment variables
cp .env.example .env
# Edit .env with your Tavily key, AWS region, and S3 bucket

# 3. Install dependencies
uv sync

# 4. Upload seed files (AGENTS.md + skills) to S3
uv run setup_backend.py

# 5. Run the agent (choose one)
uv run main.py              # Interactive CLI
uv run langgraph dev         # LangGraph Studio
```

## Running

### Interactive CLI

```bash
uv run main.py
```

Type prompts and see agent responses. Type `quit`, `exit`, or `q` to stop.

### LangGraph Studio

```bash
uv run langgraph dev
```

Opens the agent in LangGraph Studio with full HITL support, memory visualization, and debugging tools.

## Skills

| Skill | Description |
|-------|-------------|
| **linkedin-post** | Write a LinkedIn post with hook, body, CTA, and hashtags (150-300 words) |
| **twitter-post** | Write a single tweet (280 chars) or numbered thread (4-8 tweets) |

Skills are loaded on demand via progressive disclosure -- only names and descriptions appear in the initial prompt until the agent determines a skill is relevant.

## Example Prompts

### Research & Reports
```
Research the latest developments in AI agents and write a comprehensive report
```

```
Research quantum computing breakthroughs this year and create a LinkedIn post about the key findings
```

```
What are the most promising open source LLM models? Write a Twitter thread about your findings
```

### Memory Operations
```
Save this fact to semantic memory: I prefer concise reports with bullet points rather than long paragraphs
```

```
Save this rule to procedural memory: always include a TL;DR section at the top of research reports
```

```
Check your episodic memory for any previous research sessions, then research updates on those topics
```

```
What do you remember about me? Check all memory types: semantic, episodic, and procedural
```

### Research with Memory Context
```
Research the state of autonomous vehicles and save key takeaways to memory
```

## Human-in-the-Loop

The agent is configured with `interrupt_on` for `write_file` and `edit_file`. When the agent attempts to write or edit a file, execution pauses for human approval.

**In LangGraph Studio**: The interrupt appears in the UI. Approve by entering:
```json
{"decisions": [{"type": "approve"}]}
```

**In CLI mode** (`main.py`): The simple `graph.invoke()` pattern does not surface interrupts. Use LangGraph Studio for full HITL functionality.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TAVILY_API_KEY` | Yes | -- | Tavily API key for web search |
| `AWS_REGION` | Yes | -- | AWS region for S3, Bedrock, and AgentCore |
| `S3_BACKEND_BUCKET` | Yes | -- | S3 bucket name for backend storage |
| `S3_BACKEND_PREFIX` | No | `""` | S3 key prefix (e.g., `research-agent/`) |
| `AWS_ACCESS_KEY_ID` | No | -- | AWS credentials (if not using IAM role/profile) |
| `AWS_SECRET_ACCESS_KEY` | No | -- | AWS secret key |
| `AWS_SESSION_TOKEN` | No | -- | For temporary credentials |
| `LANGSMITH_API_KEY` | No | -- | LangSmith API key for tracing |
| `LANGCHAIN_TRACING_V2` | No | `false` | Enable LangSmith tracing |
| `LANGCHAIN_PROJECT` | No | -- | LangSmith project name |

No separate Anthropic API key is needed -- the agent uses Claude via Amazon Bedrock with your AWS credentials.

## S3 Storage Routes

After running the agent, you can verify files are stored at the correct S3 prefixes:

```bash
# List all objects under your prefix
aws s3 ls s3://$S3_BACKEND_BUCKET/$S3_BACKEND_PREFIX --recursive

# Check specific routes
aws s3 ls s3://$S3_BACKEND_BUCKET/${S3_BACKEND_PREFIX}memories/semantic/
aws s3 ls s3://$S3_BACKEND_BUCKET/${S3_BACKEND_PREFIX}memories/episodic/
aws s3 ls s3://$S3_BACKEND_BUCKET/${S3_BACKEND_PREFIX}memories/procedural/
aws s3 ls s3://$S3_BACKEND_BUCKET/${S3_BACKEND_PREFIX}memories/
aws s3 ls s3://$S3_BACKEND_BUCKET/${S3_BACKEND_PREFIX}skills/
aws s3 ls s3://$S3_BACKEND_BUCKET/${S3_BACKEND_PREFIX}conversation_history/
aws s3 ls s3://$S3_BACKEND_BUCKET/${S3_BACKEND_PREFIX}large_tool_results/
```

### Testing S3 Routes

1. **Skills**: After `setup_backend.py`, check that `skills/linkedin-post/SKILL.md` and `skills/twitter-post/SKILL.md` exist
2. **Memories**: Ask the agent to save something to semantic memory, then verify a file appears under `memories/semantic/`
3. **AGENTS.md**: After `setup_backend.py`, verify `memories/AGENTS.md` exists
4. **Conversation history**: After a long conversation, check `conversation_history/` for evicted chunks
5. **Large tool results**: After a search with large results, check `large_tool_results/`
