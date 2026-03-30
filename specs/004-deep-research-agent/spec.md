# Feature Specification: Deep Research Agent Example

**Feature Branch**: `004-deep-research-agent`
**Created**: 2026-03-30
**Status**: Draft
**Input**: User description: "Create a new example project called deep-research-agent under examples/ using AWS backends from deepagents-contrib-aws, with structured S3 memory (semantic/episodic/procedural), research subagent, Tavily search, skills, and human-in-the-loop."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Set Up and Run the Agent (Priority: P1)

A developer clones the repository, configures environment variables, uploads seed files to S3 via setup_backend.py, and runs the deep research agent in either CLI mode or LangGraph Studio.

**Why this priority**: Without a working setup flow, no other user stories can be tested. This is the foundation.

**Independent Test**: Can be fully tested by following the README step-by-step from a clean state, running `uv run setup_backend.py` to upload files, and then `uv run main.py` to start the CLI and send a basic prompt.

**Acceptance Scenarios**:

1. **Given** the developer has cloned the repo and configured `.env`, **When** they run `uv sync`, **Then** all dependencies install successfully (deepagents, deepagents-contrib-aws, langchain-aws, tavily-python, langgraph, python-dotenv).
2. **Given** the developer has valid AWS credentials and S3 bucket, **When** they run `uv run setup_backend.py`, **Then** the script uploads AGENTS.md to `/memories/AGENTS.md`, linkedin-post SKILL.md to `/skills/linkedin-post/SKILL.md`, and twitter-post SKILL.md to `/skills/twitter-post/SKILL.md` on S3, and skips files that already exist.
3. **Given** the setup is complete, **When** the developer runs `uv run main.py`, **Then** an interactive CLI starts accepting user input and printing agent responses.
4. **Given** the setup is complete, **When** the developer runs `uv run langgraph dev`, **Then** LangGraph Studio starts with the agent graph loaded from `graph.py:graph`.

---

### User Story 2 - Research a Topic and Generate a Report (Priority: P1)

A developer asks the agent to research a topic. The agent plans its approach, delegates research to a subagent for context isolation, synthesizes findings, and writes a structured report with citations.

**Why this priority**: This is the core value proposition -- a research agent that autonomously searches the web, delegates work to a subagent, and produces structured reports.

**Independent Test**: Can be fully tested by sending a research prompt and verifying the agent delegates to the research-agent subagent via `task()`, produces a report at `/final_report.md`, and includes inline citations with a Sources section.

**Acceptance Scenarios**:

1. **Given** the agent is running with valid Tavily and AWS credentials, **When** the user asks "Research the latest developments in AI agents and write a comprehensive report", **Then** the agent delegates to the research-agent subagent via the `task()` tool, the subagent performs web searches using tavily_search (2-5 calls), and the orchestrator synthesizes a report with inline citations [1][2][3] and a Sources section.
2. **Given** the agent has HITL enabled on write_file, **When** the agent attempts to write `/final_report.md`, **Then** the system interrupts for human approval before the file is persisted.
3. **Given** the research-agent subagent is running, **When** it searches for information, **Then** it returns structured findings with clear headings, inline citations, and a sources section, keeping its context isolated from the main orchestrator.

---

### User Story 3 - Persist Structured Long-Term Memories to S3 (Priority: P1)

A developer interacts with the agent across multiple sessions. The agent saves facts, session logs, and learned rules to separate S3 prefixes under `/memories/`. In a new session, the agent retrieves prior memories to inform its work.

**Why this priority**: Structured memory persistence is the key differentiator from the langgraph-101 agent. Without it, the agent loses all context between sessions.

**Independent Test**: Can be tested by saving a fact to `/memories/semantic/`, ending the session, starting a new session, and verifying the agent can read the previously saved memory.

**Acceptance Scenarios**:

1. **Given** the agent is running, **When** the user says "Save this fact to semantic memory: I prefer concise reports with bullet points", **Then** the agent writes a file to `/memories/semantic/user_preferences.md` on S3.
2. **Given** the agent completed a research session, **When** it saves a session log, **Then** the log is written to `/memories/episodic/` with a date-prefixed filename (e.g., `2026-03-30_ai_agents.md`) on S3.
3. **Given** the user teaches the agent a formatting rule, **When** the agent saves it, **Then** the rule is written to `/memories/procedural/` (e.g., `report_format.md`) on S3.
4. **Given** memories exist in S3 from a prior session, **When** the user starts a new session and asks "What do you remember about me?", **Then** the agent checks all three memory paths and reports what it finds.
5. **Given** the CompositeBackend has routes for `/memories/semantic/`, `/memories/episodic/`, `/memories/procedural/`, and `/memories/`, **When** a file is written to `/memories/semantic/foo.md`, **Then** it is routed to the S3 prefix `memories/semantic` (longest-prefix match), not the general `memories` prefix.

---

### User Story 4 - Generate Social Media Content from Research (Priority: P2)

After researching a topic, the developer asks the agent to create a LinkedIn post or Twitter/X thread. The agent loads the relevant skill on demand and formats the content according to the skill's instructions.

**Why this priority**: Demonstrates the skills system (progressive disclosure) and content generation, but depends on the core research flow being functional first.

**Independent Test**: Can be tested by asking the agent to write a LinkedIn post about a topic and verifying it follows the linkedin-post SKILL.md format (hook, body, CTA, hashtags, 150-300 words).

**Acceptance Scenarios**:

1. **Given** the agent has completed research on a topic, **When** the user asks "Write a LinkedIn post about your findings", **Then** the agent reads the linkedin-post SKILL.md from S3 and generates a post with a hook, 3-5 paragraphs, a call-to-action, and 3-5 hashtags.
2. **Given** the agent has completed research, **When** the user asks "Write a Twitter thread about your findings", **Then** the agent reads the twitter-post SKILL.md from S3 and generates a numbered thread of 4-8 tweets.
3. **Given** the skills directory contains linkedin-post and twitter-post skills, **When** the agent starts, **Then** only the skill names and descriptions are loaded into the system prompt (not full content), keeping the initial prompt compact.

---

### User Story 5 - Human-in-the-Loop for File Operations (Priority: P2)

When the agent attempts to write or edit a file, the system interrupts and waits for human approval before executing the operation.

**Why this priority**: HITL is important for safety but is an enhancement on top of the core research flow.

**Independent Test**: Can be tested by asking the agent to write a file and verifying that an interrupt is triggered before the write executes.

**Acceptance Scenarios**:

1. **Given** HITL is configured for write_file and edit_file, **When** the agent tries to write `/final_report.md`, **Then** an interrupt is triggered with the proposed file content.
2. **Given** an interrupt is triggered in LangGraph Studio, **When** the user approves via `{"decisions": [{"type": "approve"}]}`, **Then** the file write proceeds.
3. **Given** an interrupt is triggered, **When** the user rejects, **Then** the file write is skipped and the agent is notified.

---

### User Story 6 - Execute Code in AgentCore Sandbox (Priority: P3)

The agent can execute Python code or shell commands in the AgentCore Code Interpreter sandbox for data analysis, computation, or chart generation during research.

**Why this priority**: Code execution is a bonus capability provided by the default backend. Research and memory are the core features.

**Independent Test**: Can be tested by asking the agent to perform a calculation and verifying the output comes from the AgentCore sandbox.

**Acceptance Scenarios**:

1. **Given** the agent is running with AgentCore configured, **When** the user asks "Calculate the fibonacci sequence up to 20", **Then** the agent executes Python code in the sandbox and returns the result.
2. **Given** a file is written to a non-routed path (e.g., `/scratch.txt`), **When** the backend processes the request, **Then** it is handled by the default AgentCoreCodeInterpreterSandbox backend.

---

### Edge Cases

- What happens when the Tavily API key is invalid or missing? The tavily_search tool should fail gracefully and the research subagent should report the error.
- What happens when S3 credentials are invalid? The `_build_backend()` function should validate `S3_BACKEND_BUCKET` and `AWS_REGION` at startup and exit with a clear error message.
- What happens when the user asks to remember something but doesn't specify a memory type? The agent should categorize it based on content (fact vs experience vs rule) using the guidance in AGENTS.md and the system prompt.
- What happens when setup_backend.py is run twice? It should be idempotent -- skipping files that already exist in S3.
- What happens when the research subagent exceeds its hard limit of 5 search calls? The subagent's instructions enforce the limit as a soft limit via LLM instruction-following.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Project MUST be a self-contained example under `examples/deep_research_agent/` with its own `pyproject.toml`, `langgraph.json`, `.env.example`, `.gitignore`, and `README.md`.
- **FR-002**: `graph.py` MUST define a `graph` object using `create_deep_agent()` from the `deepagents` library, exported as the LangGraph Studio entrypoint.
- **FR-003**: `graph.py` MUST use `CompositeBackend` with `AgentCoreCodeInterpreterSandbox` as the default backend and seven S3Backend routes: `/memories/semantic/`, `/memories/episodic/`, `/memories/procedural/`, `/memories/`, `/skills/`, `/conversation_history/`, `/large_tool_results/`.
- **FR-004**: CompositeBackend routes MUST leverage longest-prefix matching so `/memories/semantic/` takes priority over `/memories/`.
- **FR-005**: `graph.py` MUST define a `tavily_search` tool using `TavilyClient` and `@tool(parse_docstring=True)` that returns up to 3 web search results formatted as markdown.
- **FR-006**: `graph.py` MUST define a research subagent dict with name `research-agent`, a system prompt with hard search limits (2-3 simple, up to 5 complex), and the `tavily_search` tool.
- **FR-007**: `graph.py` MUST configure `interrupt_on` for `write_file` and `edit_file` to enable human-in-the-loop approval.
- **FR-008**: `graph.py` MUST use `ChatBedrockConverse(model_id="us.anthropic.claude-sonnet-4-20250514-v1:0")` from `langchain_aws` as the model, configured with the AWS region from environment variables and prompt caching enabled via `supports_cache_control=True` for Claude models on Bedrock.
- **FR-009**: `graph.py` MUST include a system prompt that documents the three structured memory types (semantic, episodic, procedural) with their paths and example filenames.
- **FR-010**: `memory/AGENTS.md` MUST define the agent's identity, 5-step workflow (Plan, Research, Synthesize, Write, Remember), rules for delegation and citations, and memory guidelines for each memory type.
- **FR-011**: `skills/linkedin-post/SKILL.md` MUST contain the LinkedIn post formatting skill with YAML frontmatter (name, description), format instructions, tone guidelines, length constraints, template, and example.
- **FR-012**: `skills/twitter-post/SKILL.md` MUST contain the Twitter/X post/thread formatting skill with YAML frontmatter, single tweet and thread formats, tone guidelines, tips, and examples.
- **FR-013**: `setup_backend.py` MUST upload `memory/AGENTS.md` to `/memories/AGENTS.md`, `skills/linkedin-post/SKILL.md` to `/skills/linkedin-post/SKILL.md`, and `skills/twitter-post/SKILL.md` to `/skills/twitter-post/SKILL.md` on S3. It MUST be idempotent (skip existing files).
- **FR-014**: `main.py` MUST provide an interactive CLI that imports the graph, runs an input loop with thread_id "demo", prints agent responses, and supports quit/exit/q commands.
- **FR-015**: `graph.py` MUST follow the same `_build_backend()` and `_s3()` helper pattern as `product_support_agent/graph.py` for environment variable validation and S3Backend construction.
- **FR-016**: The agent MUST load `AGENTS.md` via `memory=["/memories/AGENTS.md"]` and skills via `skills=["/skills/"]`.
- **FR-017**: `README.md` MUST include: overview with architecture diagram, structured memory documentation (semantic/episodic/procedural table), prerequisites, quick start guide, running instructions (CLI + LangGraph Studio), skills table, at least 8 example prompts, HITL documentation, environment variables table, and S3 storage routes verification guide.

### Key Entities

- **CompositeBackend**: Routes file operations to different backends based on path prefix. Central to the agent's storage architecture.
- **S3Backend**: Persistent storage for memories, skills, conversation history, and large tool results. Each route gets its own S3 key prefix.
- **AgentCoreCodeInterpreterSandbox**: Default backend for code execution. Handles any path not matched by S3 routes.
- **Research Subagent**: Isolated agent for web research with its own context window, tools, and hard limits on search calls.
- **Structured Memory**: Three-type memory system (semantic facts, episodic experiences, procedural rules) mapped to filesystem paths and S3 prefixes.
- **Skills**: On-demand capability bundles (linkedin-post, twitter-post) loaded via progressive disclosure.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can set up the agent from scratch in under 10 minutes by following the README (clone, configure .env, uv sync, setup_backend.py, run).
- **SC-002**: The agent successfully delegates research to the subagent and produces a report with at least 3 inline citations and a Sources section.
- **SC-003**: Memories written to `/memories/semantic/`, `/memories/episodic/`, and `/memories/procedural/` are persisted to separate S3 prefixes and retrievable in a new session.
- **SC-004**: Skills are loaded on demand -- only skill names and descriptions appear in the initial prompt, with full content loaded when the agent determines a skill is relevant.
- **SC-005**: File write and edit operations trigger HITL interrupts in LangGraph Studio mode, and the agent proceeds only after human approval.
- **SC-006**: The setup_backend.py script uploads all 3 seed files to S3 on first run and skips them on subsequent runs (idempotent).
- **SC-007**: The agent runs successfully in both CLI mode (`uv run main.py`) and LangGraph Studio mode (`uv run langgraph dev`).
- **SC-008**: All 7 S3 routes are correctly configured and files written to each path land in the expected S3 prefix.

## Clarifications

### Session 2026-03-30

- No critical ambiguities detected. Spec coverage is complete across all taxonomy categories (functional scope, data model, UX flow, integrations, edge cases, constraints, terminology, completion signals).

## Assumptions

- The developer has Python 3.11+ and `uv` installed.
- The developer has valid AWS credentials with access to S3 and Bedrock AgentCore.
- The developer has a Tavily API key (free tier available at tavily.com).
- The developer has AWS credentials with Bedrock model invocation access (Claude models via Bedrock, no separate Anthropic API key needed).
- The S3 bucket referenced by `S3_BACKEND_BUCKET` already exists and the developer has read/write access.
- The `deepagents>=0.4.0` package is available on PyPI and provides `create_deep_agent`, `CompositeBackend`, and all middleware.
- The `deepagents-contrib-aws>=0.2.0` package is available on PyPI and provides `S3Backend` and `AgentCoreCodeInterpreterSandbox`.
- AGENTS.md content and skills content are provided verbatim from langgraph-101 reference with memory path adaptations.
- The `graph.py` backend pattern (env var validation, `_s3()` helper, `_build_backend()`) is adapted from `product_support_agent/graph.py` with route additions for structured memory.
