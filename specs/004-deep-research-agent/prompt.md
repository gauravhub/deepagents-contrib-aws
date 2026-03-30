# Deep Research Agent — speckit.fleet prompt

Create a new example project called "deep-research-agent" under `examples/` (sibling to the existing `examples/product_support_agent`). This is a research agent modeled on the LangGraph-101 deep research agent pattern (see `/tmp/langgraph-101/agents/deep_agent/`) but using AWS backends from `deepagents-contrib-aws`.

## What This Agent Does

A web research agent that can:

- Search the web using Tavily
- Delegate research to a dedicated research subagent (context isolation)
- Synthesize findings into reports
- Generate LinkedIn posts and Twitter/X threads from research (via skills)
- Persist structured long-term memories to S3 — organized into semantic, episodic, and procedural memory types (inspired by the CoALA paper)
- Execute code in AgentCore Code Interpreter sandbox
- Require human approval before writing/editing files (HITL)

## Project Structure

```
examples/deep_research_agent/
├── .env.example
├── .gitignore
├── langgraph.json
├── pyproject.toml
├── README.md
├── main.py                    # Interactive CLI (same pattern as product_support_agent/main.py)
├── graph.py                   # LangGraph agent definition
├── setup_backend.py           # Upload skills + AGENTS.md to S3
├── memory/
│   └── AGENTS.md              # Agent identity (research assistant workflow)
└── skills/
    ├── linkedin-post/
    │   └── SKILL.md           # LinkedIn post formatting skill
    └── twitter-post/
        └── SKILL.md           # Twitter/X thread formatting skill
```

## graph.py — Agent Definition

Follow the exact same backend architecture as `product_support_agent/graph.py` (use `_build_backend()`, `_s3()` helper, env var validation, `load_dotenv()` at top) but adapted for research.

### Backend (CompositeBackend)

- **Default**: `AgentCoreCodeInterpreterSandbox` — for code execution (data analysis, chart generation, etc.)
- **`/memories/`** → `S3Backend` — top-level memory route; `/memories/AGENTS.md` lives here
- **`/memories/semantic/`** → `S3Backend` (separate prefix `memories/semantic`) — facts & knowledge: user preferences, project context, topic summaries
- **`/memories/episodic/`** → `S3Backend` (separate prefix `memories/episodic`) — past experiences: dated research session logs, interaction summaries
- **`/memories/procedural/`** → `S3Backend` (separate prefix `memories/procedural`) — instructions & rules: report formatting rules, citation standards, learned workflows
- **`/skills/`** → `S3Backend` — skill library (linkedin-post, twitter-post)
- **`/conversation_history/`** → `S3Backend` — archived conversation chunks (evicted by summarization middleware)
- **`/large_tool_results/`** → `S3Backend` — oversized tool outputs (search results, reports)

**Important**: CompositeBackend uses longest-prefix matching, so `/memories/semantic/` takes priority over `/memories/`. All seven routes must be defined in the `routes` dict. Use the `_s3()` helper from product-support-agent pattern to construct each S3Backend with the correct prefix suffix.

Example route construction (inside `_build_backend()`):

```python
routes = {
    "/memories/semantic/": _s3("memories/semantic"),
    "/memories/episodic/": _s3("memories/episodic"),
    "/memories/procedural/": _s3("memories/procedural"),
    "/memories/": _s3("memories"),
    "/skills/": _s3("skills"),
    "/conversation_history/": _s3("conversation_history"),
    "/large_tool_results/": _s3("large_tool_results"),
}
```

### Research Subagent

Define a research subagent dict (NOT a separate file) inside `graph.py`, modeled on the langgraph-101 pattern:

```python
from datetime import datetime

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
```

### Custom Tools

`tavily_search` — web search using `TavilyClient`, returns up to 3 results formatted as markdown with title, URL, and content. Use the `@tool(parse_docstring=True)` decorator from `langchain_core.tools`. Copy the exact implementation from `/tmp/langgraph-101/agents/deep_agent/agent.py`.

### System Prompt

The system prompt in `graph.py` should be minimal (since AGENTS.md carries the main instructions) but must include the structured memory guidance so the agent knows how to route memories:

```python
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
```

### Agent Creation

```python
graph = create_deep_agent(
    model=ChatAnthropic(model="claude-sonnet-4-20250514"),
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
```

### Model

Use `ChatAnthropic(model="claude-sonnet-4-20250514")` from `langchain_anthropic`. Import at top of `graph.py`.

## memory/AGENTS.md

```markdown
# Research Assistant

You are an expert research assistant that can search the web, synthesize findings and produce polished reports and content.

## Workflow

1. **Plan** -- Use `write_todos` to break the task into steps
2. **Research** -- Delegate research to the `research-agent` using the `task()` tool
3. **Synthesize** -- Combine findings into a comprehensive report
4. **Write** -- Save the final report to `/final_report.md`
5. **Remember** -- Save key takeaways to the appropriate memory path:
   - Facts & knowledge → `/memories/semantic/`
   - Session logs & experiences → `/memories/episodic/`
   - Rules & formatting standards → `/memories/procedural/`

## Rules

- Delegate research to the research-agent rather than searching directly
- After receiving research results, synthesize and write the report yourself
- Consolidate citations -- each unique URL gets one number [1], [2], [3]
- End reports with a Sources section listing all referenced URLs
- Check for relevant skills when asked to create specific content formats (e.g., social media posts)
- Before starting new research, check `/memories/semantic/` and `/memories/episodic/` for prior findings on the topic

## Memory Guidelines

- **Semantic memory** (`/memories/semantic/`): Save factual summaries, user preferences, and topic overviews. Name files descriptively: `ai_agents_overview.md`, `user_preferences.md`
- **Episodic memory** (`/memories/episodic/`): Save dated session logs after each research task. Use date-prefixed names: `2025-03-30_quantum_computing.md`
- **Procedural memory** (`/memories/procedural/`): Save learned rules about how to format outputs, what citation style to use, or any workflow the user teaches you

## File Path Formatting

When referencing file paths in responses, always use backtick formatting like `/final_report.md` -- never use markdown links, since files live in the agent's virtual filesystem and are not clickable.
```

## skills/ — Copy from langgraph-101

### skills/linkedin-post/SKILL.md

Copy the exact content from `/tmp/langgraph-101/agents/deep_agent/skills/linkedin-post/SKILL.md`:

```markdown
---
name: linkedin-post
description: Write a LinkedIn post based on research findings or a given topic. Use this skill when asked to create LinkedIn content, professional posts, or thought leadership pieces.
---

# LinkedIn Post Skill

## Format

- **Hook**: Start with a bold opening line that grabs attention (this appears before the "see more" cut)
- **Body**: 3-5 short paragraphs, each 1-2 sentences
- Use line breaks between paragraphs for readability
- Include 1-2 relevant emojis per paragraph (don't overdo it)
- End with a call-to-action or question to drive engagement
- Add 3-5 relevant hashtags at the bottom

## Tone

- Professional but conversational
- Share insights, not just information
- Use "I" statements and personal perspective where appropriate
- Avoid jargon unless the audience expects it

## Length

- Ideal: 150-300 words
- LinkedIn truncates after ~210 characters, so the first line must hook the reader

## Template

\```
[Bold hook / surprising stat / question]

[Context -- why this matters]

[Key insight 1]

[Key insight 2]

[Key insight 3 or personal takeaway]

[Call to action / question for engagement]

#hashtag1 #hashtag2 #hashtag3
\```

## Example

\```
Most AI agents fail not because of the model -- but because of context management.

After researching the latest agent frameworks, one pattern keeps emerging:
the best agents treat their context window like a scarce resource.

Here's what separates good agents from great ones:

1. They offload intermediate results to a filesystem instead of keeping everything in context
2. They delegate to subagents for isolation -- the main agent only sees summaries
3. They use progressive disclosure -- loading instructions only when relevant

The shift from "bigger context window" to "smarter context management" is where
the real breakthroughs are happening.

What patterns have you seen work best in your agent architectures?

#AIAgents #LangChain #LangGraph #ContextEngineering
\```
```

### skills/twitter-post/SKILL.md

Copy the exact content from `/tmp/langgraph-101/agents/deep_agent/skills/twitter-post/SKILL.md`:

```markdown
---
name: twitter-post
description: Write a Twitter/X post or thread based on research findings or a given topic. Use this skill when asked to create tweets, X posts, or social media threads.
---

# Twitter/X Post Skill

## Single Tweet Format

- Maximum 280 characters
- Lead with the most compelling point
- Use numbers or data when possible
- End with a link placeholder or call-to-action
- 1-2 hashtags max (optional)

## Thread Format (for longer content)

- **Tweet 1**: Hook + preview of what's coming (e.g., "A thread on X:" or "Here's what I found:")
- **Tweets 2-N**: One idea per tweet, numbered (1/, 2/, 3/)
- **Final tweet**: Summary + call-to-action + link
- Keep each tweet self-contained (people share individual tweets)
- 4-8 tweets is the sweet spot for engagement

## Tone

- Concise and punchy
- Opinionated takes perform better than neutral summaries
- Use plain language -- no corporate speak
- Contrarian or surprising angles get more engagement

## Tips

- Front-load the value (no throat-clearing or preambles)
- Use line breaks within tweets for readability
- Avoid hashtags in threads (they look spammy) -- save them for single tweets
- Numbers and lists catch the eye in a feed

## Example Single Tweet

\```
AI agents that manage their context window well outperform those with 10x more tools.

The secret isn't more capabilities -- it's smarter context engineering.
\```

## Example Thread

\```
Thread: What makes AI agents actually work in production?

1/ It's not the model size. It's context management.

The best agents treat their context window like RAM -- offloading to filesystem, summarizing aggressively, loading info on demand.

2/ Subagents are the key to scaling.

Instead of one agent doing everything, delegate to specialists. The main agent only sees the summary, not 50 intermediate tool calls.

3/ Skills > giant system prompts.

Progressive disclosure: load detailed instructions only when the task needs them. Your agent's prompt stays clean until it matters.

4/ Memory needs structure.

Semantic (facts), episodic (experiences), procedural (rules) -- route them to different backends so they persist appropriately.

5/ The takeaway: the best agent architectures are about information flow, not raw capability.

What patterns are you using? Reply with your favorite agent architecture trick.
\```
```

## setup_backend.py

Follow the same pattern as `product_support_agent/setup_backend.py`:

- Upload `skills/linkedin-post/SKILL.md` → `/skills/linkedin-post/SKILL.md`
- Upload `skills/twitter-post/SKILL.md` → `/skills/twitter-post/SKILL.md`
- Upload `memory/AGENTS.md` → `/memories/AGENTS.md`
- Idempotent (skip if file already exists in S3), read env vars for S3 config
- Print upload status (UPLOAD, SKIP, MISSING, ERROR)
- Summary at end showing uploaded and skipped counts

## main.py

Same interactive CLI pattern as `product_support_agent/main.py`:

- Import `graph` from `graph.py`
- Input loop with `thread_id` "demo"
- Print agent responses
- Support quit/exit/q commands and Ctrl+C/EOF

## pyproject.toml

```toml
[project]
name = "deep-research-agent"
version = "0.1.0"
description = "Deep research agent example using deepagents with AWS backends (S3 + AgentCore)"
requires-python = ">=3.11"
dependencies = [
    "deepagents>=0.4.0",
    "deepagents-contrib-aws>=0.2.0",
    "langchain-anthropic",
    "tavily-python",
    "python-dotenv",
    "langgraph",
]
```

## langgraph.json

```json
{
  "dependencies": ["."],
  "graphs": {
    "agent": "./graph.py:graph"
  },
  "env": ".env"
}
```

## .env.example

```
# Required: Anthropic API key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Required: Tavily API key for web search
TAVILY_API_KEY=your-tavily-api-key

# Required: AWS region
AWS_REGION=us-west-2

# Required: S3 bucket for backend storage
S3_BACKEND_BUCKET=your-bucket-name

# Optional: S3 key prefix (e.g., "research-agent/")
S3_BACKEND_PREFIX=

# Optional: AWS credentials (if not using IAM role/profile)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_SESSION_TOKEN=

# Optional: LangSmith tracing
LANGSMITH_API_KEY=
LANGCHAIN_TRACING_V2=false
LANGCHAIN_PROJECT=deep-research-agent
```

## .gitignore

Same as `product_support_agent/.gitignore` — ignore `.env`, `.venv`, `__pycache__`, `.langgraph_api/`, OS files, IDE files.

## README.md

Comprehensive README with these sections:

### 1. Overview
What the agent does (research + content generation with structured long-term memory). Include a text-based architecture diagram showing:

```
User Request
    │
    ▼
┌─────────────────────────────────────────────┐
│  Deep Research Agent (Orchestrator)          │
│  - Plans with write_todos                   │
│  - Delegates to research-agent subagent     │
│  - Synthesizes reports                      │
│  - Loads skills on demand                   │
│  - HITL on file writes                      │
└─────────┬───────────────────────────────────┘
          │
    ┌─────┴─────┐
    │ Subagent  │
    │ research- │
    │ agent     │
    │ (tavily)  │
    └───────────┘
          │
          ▼
┌─────────────────────────────────────────────┐
│  CompositeBackend                           │
│                                             │
│  Default: AgentCore Code Interpreter        │
│                                             │
│  S3 Routes:                                 │
│  /memories/semantic/    → S3 (facts)        │
│  /memories/episodic/    → S3 (experiences)  │
│  /memories/procedural/  → S3 (rules)        │
│  /memories/             → S3 (/memories/AGENTS.md) │
│  /skills/               → S3 (SKILL.md)     │
│  /conversation_history/ → S3 (evicted msgs) │
│  /large_tool_results/   → S3 (big outputs)  │
└─────────────────────────────────────────────┘
```

### 2. Structured Memory (Semantic / Episodic / Procedural)
Explain the three memory types with a table (based on notebook Cell 69):

| Memory Type | Path | What It Stores | Example Files |
|-------------|------|---------------|---------------|
| **Semantic** | `/memories/semantic/` | Facts & knowledge | `user_preferences.md`, `ai_agents_overview.md` |
| **Episodic** | `/memories/episodic/` | Past experiences | `2025-03-30_quantum_research.md` |
| **Procedural** | `/memories/procedural/` | Instructions & rules | `report_format.md`, `citation_style.md` |

Explain that CompositeBackend longest-prefix matching ensures `/memories/semantic/` routes to its own S3 prefix, separate from `/memories/`.

### 3. Prerequisites
- Python 3.11+, uv
- AWS credentials with access to S3 and Bedrock AgentCore
- Tavily API key (free at tavily.com)
- Anthropic API key

### 4. Quick Start
Step by step: clone, cd, copy `.env.example` → `.env`, fill in keys, `uv sync`, `uv run setup_backend.py`, then choose run mode.

### 5. Running
Two modes:
- Interactive CLI: `uv run main.py`
- LangGraph Studio: `uv run langgraph dev`

### 6. Skills
Table listing linkedin-post and twitter-post skills with descriptions.

### 7. Example Prompts
At least 8 example prompts showing different capabilities including memory usage:

- "Research the latest developments in AI agents and write a comprehensive report"
- "Research quantum computing breakthroughs this year and create a LinkedIn post about the key findings"
- "What are the most promising open source LLM models? Write a Twitter thread about your findings"
- "Research the state of autonomous vehicles and save key takeaways to memory"
- "Save this fact to semantic memory: I prefer concise reports with bullet points rather than long paragraphs"
- "Check your episodic memory for any previous research sessions, then research updates on those topics"
- "Save this rule to procedural memory: always include a TL;DR section at the top of research reports"
- "What do you remember about me? Check all memory types: semantic, episodic, and procedural"

### 8. Human-in-the-Loop
Explain that `write_file` and `edit_file` require approval. In LangGraph Studio, approve via the interrupt UI (enter `{"decisions": [{"type": "approve"}]}`). In CLI mode, approval is automatic.

### 9. Environment Variables
Full table of all env vars with required/optional and descriptions.

### 10. S3 Storage Routes
How to verify each route is working — similar to product_support_agent README. Include instructions to check the S3 bucket for files under each prefix (`memories/semantic/`, `memories/episodic/`, `memories/procedural/`, `skills/`, etc.).

## Key Differences from product_support_agent

1. **Research-focused** instead of product support
2. **Has a research subagent** for delegated, context-isolated web research
3. **Has `tavily_search` custom tool** for web search
4. **Skills are content-generation focused** (LinkedIn, Twitter) not troubleshooting
5. **HITL on file writes** (`interrupt_on`) — product_support_agent doesn't have this
6. **Structured memory** — semantic/episodic/procedural S3 sub-routes under `/memories/`
7. **Uses `ChatAnthropic` model directly** instead of relying on default

## Key Differences from langgraph-101 deep_agent

1. **Uses S3Backend for `/memories/`** instead of StoreBackend — durable cross-thread memory via S3, with semantic/episodic/procedural sub-routes each getting their own S3 prefix
2. **Uses AgentCoreCodeInterpreterSandbox** as default backend — can execute code
3. **Has `/conversation_history/` and `/large_tool_results/` S3 routes** — production-grade context management
4. **Has `setup_backend.py`** — uploads skills and AGENTS.md to S3 before first run
5. **Standalone project** with its own `pyproject.toml`, not part of a monorepo
