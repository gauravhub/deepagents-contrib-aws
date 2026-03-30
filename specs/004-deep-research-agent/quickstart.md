# Quickstart: Deep Research Agent Example

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- AWS credentials with access to S3 and Bedrock AgentCore
- Tavily API key (free at [tavily.com](https://tavily.com))
- Anthropic API key

## Setup

```bash
# Navigate to the example
cd examples/deep_research_agent

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys and AWS config

# Install dependencies
uv sync

# Upload seed files (AGENTS.md + skills) to S3
uv run setup_backend.py
```

## Run

### Option 1: Interactive CLI
```bash
uv run main.py
```

### Option 2: LangGraph Studio
```bash
uv run langgraph dev
```

## Example Prompts

```
Research the latest developments in AI agents and write a comprehensive report
```

```
Save this fact to semantic memory: I prefer concise reports with bullet points
```

```
What do you remember about me? Check all memory types.
```

```
Write a LinkedIn post about your research findings
```
