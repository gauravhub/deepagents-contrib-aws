# Implementation Plan: Deep Research Agent Example

**Branch**: `004-deep-research-agent` | **Date**: 2026-03-30 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-deep-research-agent/spec.md`

## Summary

Create a self-contained example project `examples/deep_research_agent/` that demonstrates a web research agent using AWS backends from `deepagents-contrib-aws`. The agent uses `CompositeBackend` with `AgentCoreCodeInterpreterSandbox` (default) and 7 S3Backend routes including structured long-term memory (semantic/episodic/procedural). It delegates research to a subagent with Tavily search, loads LinkedIn and Twitter content skills on demand, and requires human approval for file writes.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: deepagents>=0.4.0, deepagents-contrib-aws>=0.2.0, langchain-aws, tavily-python, langgraph, python-dotenv
**Storage**: Amazon S3 via S3Backend (7 route prefixes), AgentCoreCodeInterpreterSandbox (default)
**Testing**: Manual testing via CLI and LangGraph Studio (example project, not a library)
**Target Platform**: Linux/macOS/Windows (developer workstation)
**Project Type**: Example application (standalone under examples/)
**Performance Goals**: N/A (example project)
**Constraints**: Must follow existing product_support_agent patterns; all content for AGENTS.md and skills copied from langgraph-101 reference
**Scale/Scope**: Single developer setup, demonstration purposes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution is a blank template with no project-specific principles defined. No gates to enforce. PASS.

## Project Structure

### Documentation (this feature)

```text
specs/004-deep-research-agent/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
examples/deep_research_agent/
├── .env.example             # Environment variable template
├── .gitignore               # Git ignore rules
├── langgraph.json           # LangGraph Studio configuration
├── pyproject.toml           # Python project metadata and dependencies
├── README.md                # Comprehensive documentation
├── main.py                  # Interactive CLI entry point
├── graph.py                 # LangGraph agent definition (CompositeBackend + subagent)
├── setup_backend.py         # Upload skills + AGENTS.md to S3
├── memory/
│   └── AGENTS.md            # Agent identity and workflow instructions
└── skills/
    ├── linkedin-post/
    │   └── SKILL.md         # LinkedIn post formatting skill
    └── twitter-post/
        └── SKILL.md         # Twitter/X thread formatting skill
```

**Structure Decision**: Single self-contained example project under `examples/deep_research_agent/`, mirroring the existing `examples/product_support_agent/` layout. No tests directory (example project validated manually). No src/ directory (flat layout with graph.py as entrypoint).

## Implementation Approach

### File-by-File Plan

#### 1. `pyproject.toml` (new)
- Standard Python project metadata
- Dependencies: deepagents>=0.4.0, deepagents-contrib-aws>=0.2.0, langchain-aws, tavily-python, python-dotenv, langgraph
- requires-python >= 3.11

#### 2. `langgraph.json` (new)
- Points to `./graph.py:graph` as the agent entrypoint
- References `.env` for environment variables

#### 3. `.env.example` (new)
- Template with all required/optional env vars: TAVILY_API_KEY, AWS_REGION, S3_BACKEND_BUCKET, S3_BACKEND_PREFIX, AWS credentials (also used for Bedrock model access), LangSmith tracing

#### 4. `.gitignore` (new)
- Copy from product_support_agent with same patterns (.env, .venv, __pycache__, .langgraph_api/, OS/IDE files)

#### 5. `graph.py` (new) -- Core file
- `load_dotenv()` at top
- Import `ChatBedrockConverse` from `langchain_aws`
- Import `create_deep_agent` from `deepagents`
- Import `CompositeBackend` from `deepagents.backends.composite`
- Import `AgentCoreCodeInterpreterSandbox`, `S3Backend` from `deepagents_contrib_aws`
- Import `TavilyClient` from `tavily`, `tool` from `langchain_core.tools`
- Define `SYSTEM_PROMPT` with structured memory documentation (semantic/episodic/procedural paths and examples)
- Define `tavily_search` tool: `@tool(parse_docstring=True)`, uses `TavilyClient().search()`, returns up to 3 results as markdown
- Define `RESEARCHER_INSTRUCTIONS` with current date, hard limits (2-3 simple, 5 complex), output format
- Define `research_subagent` dict: name="research-agent", description, system_prompt, tools=[tavily_search]
- Define `_build_backend()` function:
  - Validate `S3_BACKEND_BUCKET` and `AWS_REGION` env vars (exit with error if missing)
  - Normalize `S3_BACKEND_PREFIX`
  - Define `_s3(suffix)` helper returning `S3Backend(bucket, prefix, region_name)`
  - Create `AgentCoreCodeInterpreterSandbox(region_name=region)`
  - Build routes dict with 7 entries (3 memory sub-types + memories + skills + conversation_history + large_tool_results)
  - Return `CompositeBackend(default=sandbox, routes=routes)`
- Call `backend = _build_backend()` at module level
- Create `graph = create_deep_agent(model=ChatBedrockConverse(model_id="us.anthropic.claude-sonnet-4-20250514-v1:0", region_name=region), tools=[tavily_search], system_prompt=SYSTEM_PROMPT, memory=["/memories/AGENTS.md"], skills=["/skills/"], subagents=[research_subagent], backend=backend, interrupt_on={"write_file": True, "edit_file": True})`

#### 6. `main.py` (new)
- Copy pattern from product_support_agent/main.py
- Change title to "Deep Research Agent"
- Import `graph` from `graph`

#### 7. `setup_backend.py` (new)
- Copy pattern from product_support_agent/setup_backend.py
- Update `FILES_TO_UPLOAD` to 3 entries: memory/AGENTS.md, skills/linkedin-post/SKILL.md, skills/twitter-post/SKILL.md
- Same idempotent upload logic

#### 8. `memory/AGENTS.md` (new)
- Research assistant identity with 5-step workflow (Plan, Research, Synthesize, Write, Remember)
- Memory guidelines for semantic/episodic/procedural types
- Rules for delegation, citations, file path formatting
- Content adapted from langgraph-101 AGENTS.md with structured memory paths

#### 9. `skills/linkedin-post/SKILL.md` (new)
- Copy from `/tmp/langgraph-101/agents/deep_agent/skills/linkedin-post/SKILL.md`
- YAML frontmatter + format/tone/length/template/example

#### 10. `skills/twitter-post/SKILL.md` (new)
- Copy from `/tmp/langgraph-101/agents/deep_agent/skills/twitter-post/SKILL.md`
- YAML frontmatter + single tweet/thread format/tone/tips/examples

#### 11. `README.md` (new)
- Overview with text-based architecture diagram
- Structured Memory section with semantic/episodic/procedural table
- Prerequisites
- Quick Start (clone, .env, uv sync, setup_backend.py, run)
- Running (CLI + LangGraph Studio)
- Skills table
- 8+ example prompts including memory-specific ones
- HITL documentation
- Environment Variables table
- S3 Storage Routes verification guide

### Dependencies Between Files

```
pyproject.toml (no deps - create first)
langgraph.json (no deps)
.env.example (no deps)
.gitignore (no deps)
memory/AGENTS.md (no deps - content file)
skills/linkedin-post/SKILL.md (no deps - content file)
skills/twitter-post/SKILL.md (no deps - content file)
graph.py (depends on: pyproject.toml for imports)
main.py (depends on: graph.py)
setup_backend.py (depends on: pyproject.toml for imports, memory/ and skills/ for content)
README.md (depends on: all other files for accurate documentation)
```

### Parallelization Opportunities

Group 1 (no dependencies, all independent):
- pyproject.toml, langgraph.json, .env.example, .gitignore

Group 2 (content files, all independent):
- memory/AGENTS.md, skills/linkedin-post/SKILL.md, skills/twitter-post/SKILL.md

Group 3 (code files, depend on Group 1):
- graph.py (core logic)

Group 4 (code files, depend on graph.py):
- main.py, setup_backend.py

Group 5 (documentation, depends on all):
- README.md

## Complexity Tracking

No constitution violations to justify. This is a straightforward example project following established patterns.
