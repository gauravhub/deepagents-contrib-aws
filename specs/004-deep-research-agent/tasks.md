# Tasks: Deep Research Agent Example

**Input**: Design documents from `/specs/004-deep-research-agent/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Tests**: Not requested. This is an example project validated manually.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Project Initialization)

**Purpose**: Create project directory and configuration files

<!-- parallel-group: 1 (max 3 concurrent) -->
- [x] T001 [P] Create examples/deep_research_agent/pyproject.toml with project metadata and dependencies (deepagents>=0.4.0, deepagents-contrib-aws>=0.2.0, langchain-aws, tavily-python, python-dotenv, langgraph), requires-python>=3.11
- [x] T002 [P] Create examples/deep_research_agent/langgraph.json pointing to ./graph.py:graph with env .env
- [x] T003 [P] Create examples/deep_research_agent/.env.example with all required/optional env vars (TAVILY_API_KEY, AWS_REGION, S3_BACKEND_BUCKET, S3_BACKEND_PREFIX, AWS credentials for S3/Bedrock/AgentCore, LangSmith tracing). No ANTHROPIC_API_KEY needed — model uses Bedrock via AWS credentials.

<!-- parallel-group: 2 (max 3 concurrent) -->
- [x] T004 [P] Create examples/deep_research_agent/.gitignore matching product_support_agent patterns (.env, .venv, __pycache__, .langgraph_api/, OS/IDE files)

---

## Phase 2: Content Files (Seed Data)

**Purpose**: Create AGENTS.md and skill files that will be uploaded to S3

<!-- parallel-group: 3 (max 3 concurrent) -->
- [x] T005 [P] Create examples/deep_research_agent/memory/AGENTS.md with research assistant identity, 5-step workflow (Plan, Research, Synthesize, Write, Remember), delegation rules, citation rules, and memory guidelines for semantic/episodic/procedural types. Adapt from langgraph-101 AGENTS.md with structured memory paths.
- [x] T006 [P] Create examples/deep_research_agent/skills/linkedin-post/SKILL.md — copy exact content from /tmp/langgraph-101/agents/deep_agent/skills/linkedin-post/SKILL.md (YAML frontmatter + format/tone/length/template/example)
- [x] T007 [P] Create examples/deep_research_agent/skills/twitter-post/SKILL.md — copy exact content from /tmp/langgraph-101/agents/deep_agent/skills/twitter-post/SKILL.md (YAML frontmatter + single tweet/thread format/tone/tips/examples)

**Checkpoint**: All configuration and content files ready. Code files can now be created.

---

## Phase 3: User Story 1 - Set Up and Run the Agent (Priority: P1) — MVP

**Goal**: Developer can install dependencies, upload seed files to S3, and run the agent in CLI or LangGraph Studio mode.

**Independent Test**: Follow README from clean state: uv sync, setup_backend.py uploads 3 files, main.py starts CLI accepting prompts.

### Implementation for User Story 1

<!-- sequential -->
- [x] T008 [US1] Create examples/deep_research_agent/graph.py with: load_dotenv() at top; SYSTEM_PROMPT with structured memory documentation (semantic/episodic/procedural paths and examples); tavily_search tool using TavilyClient and @tool(parse_docstring=True) returning up to 3 results as markdown; RESEARCHER_INSTRUCTIONS with current date and hard limits; research_subagent dict (name="research-agent", tools=[tavily_search]); _build_backend() with env var validation, _s3() helper, AgentCoreCodeInterpreterSandbox default, 7 S3Backend routes (/memories/semantic/, /memories/episodic/, /memories/procedural/, /memories/, /skills/, /conversation_history/, /large_tool_results/); graph = create_deep_agent(model=ChatBedrockConverse(model_id="us.anthropic.claude-sonnet-4-20250514-v1:0", region_name=region), tools, system_prompt, memory=["/memories/AGENTS.md"], skills=["/skills/"], subagents=[research_subagent], backend=backend, interrupt_on={"write_file": True, "edit_file": True}). Follow product_support_agent/graph.py pattern for _build_backend() and _s3().

<!-- parallel-group: 4 (max 3 concurrent) -->
- [x] T009 [P] [US1] Create examples/deep_research_agent/main.py — interactive CLI importing graph from graph.py, input loop with thread_id "demo", prints agent responses, supports quit/exit/q and Ctrl+C/EOF. Follow product_support_agent/main.py pattern, change title to "Deep Research Agent".
- [x] T010 [P] [US1] Create examples/deep_research_agent/setup_backend.py — upload 3 seed files (memory/AGENTS.md → /memories/AGENTS.md, skills/linkedin-post/SKILL.md → /skills/linkedin-post/SKILL.md, skills/twitter-post/SKILL.md → /skills/twitter-post/SKILL.md) to S3. Idempotent (skip existing). Follow product_support_agent/setup_backend.py pattern with updated FILES_TO_UPLOAD.

**Checkpoint**: Agent runs in CLI mode. setup_backend.py uploads seed files. LangGraph Studio can load graph.py:graph. US1 is the MVP.

---

## Phase 4: User Story 2 - Research and Report Generation (Priority: P1)

**Goal**: Agent delegates research to subagent, synthesizes findings, writes report with citations.

**Independent Test**: Send "Research AI agents and write a report" — agent uses task() to delegate to research-agent, produces /final_report.md with [1][2][3] citations and Sources section.

*No additional implementation tasks needed — US2 is fully handled by graph.py (T008) which defines the research subagent, tavily_search tool, and AGENTS.md workflow. Validation is manual.*

**Checkpoint**: Research delegation and report generation working.

---

## Phase 5: User Story 3 - Structured Long-Term Memory (Priority: P1)

**Goal**: Memories persist to separate S3 prefixes (semantic/episodic/procedural) and survive across sessions.

**Independent Test**: Save a fact to /memories/semantic/, end session, start new session, verify agent retrieves it.

*No additional implementation tasks needed — US3 is fully handled by graph.py (T008) which defines the 7 CompositeBackend routes with longest-prefix matching, and by AGENTS.md (T005) which defines memory guidelines. Validation is manual.*

**Checkpoint**: Structured memory persistence working across sessions.

---

## Phase 6: User Story 4 - Social Media Content Generation (Priority: P2)

**Goal**: Agent loads skills on demand and generates LinkedIn posts and Twitter threads from research.

**Independent Test**: Ask agent to write a LinkedIn post — it reads SKILL.md from S3 and produces formatted content (hook, body, CTA, hashtags).

*No additional implementation tasks needed — US4 is fully handled by graph.py (T008) which configures skills=["/skills/"], and by the SKILL.md files (T006, T007). Validation is manual.*

**Checkpoint**: Skills progressive disclosure and content generation working.

---

## Phase 7: User Story 5 - Human-in-the-Loop (Priority: P2)

**Goal**: File writes and edits trigger interrupts requiring human approval.

**Independent Test**: Ask agent to write a file — interrupt triggers in LangGraph Studio, approve to proceed.

*No additional implementation tasks needed — US5 is fully handled by graph.py (T008) which configures interrupt_on={"write_file": True, "edit_file": True}. Validation requires LangGraph Studio.*

**Checkpoint**: HITL interrupts working in LangGraph Studio.

---

## Phase 8: User Story 6 - Code Execution in AgentCore (Priority: P3)

**Goal**: Agent can execute Python code in AgentCore sandbox for computation/analysis.

**Independent Test**: Ask agent to calculate something — it runs code in the sandbox and returns results.

*No additional implementation tasks needed — US6 is fully handled by graph.py (T008) which uses AgentCoreCodeInterpreterSandbox as the default backend. Validation is manual.*

**Checkpoint**: Code execution working via default backend.

---

## Phase 9: Polish & Documentation

**Purpose**: Comprehensive README documenting the complete agent

<!-- sequential -->
- [x] T011 Create examples/deep_research_agent/README.md with: overview and text-based architecture diagram showing CompositeBackend routing; Structured Memory section with semantic/episodic/procedural table (memory type, path, what it stores, example files); Prerequisites (Python 3.11+, uv, AWS credentials, Tavily key, Anthropic key); Quick Start (clone, .env, uv sync, setup_backend.py, run); Running section (CLI: uv run main.py, LangGraph Studio: uv run langgraph dev); Skills table (linkedin-post, twitter-post with descriptions); at least 8 example prompts including memory-specific ones; HITL documentation (approve via {"decisions": [{"type": "approve"}]} in Studio, CLI limitation note); Environment Variables table (all vars with required/optional and descriptions); S3 Storage Routes verification guide (how to check each prefix in S3).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — can start immediately
- **Phase 2 (Content)**: No dependencies — can run in parallel with Phase 1
- **Phase 3 (US1 - Core)**: Depends on Phase 1 + Phase 2 completion (needs pyproject.toml for imports, needs content files for references)
- **Phases 4-8 (US2-US6)**: No additional code tasks — covered by Phase 3 graph.py
- **Phase 9 (Polish)**: Depends on all other phases for accurate documentation

### Within Phase 3

- T008 (graph.py) must complete before T009 (main.py) and T010 (setup_backend.py) — main.py imports from graph.py

### Parallel Opportunities

- Phase 1: T001, T002, T003 can run in parallel (different files)
- Phase 2: T005, T006, T007 can run in parallel (different files)
- Phase 3: T009, T010 can run in parallel after T008 completes (different files)

---

## Parallel Example: Phase 1 + Phase 2

```bash
# Group 1: All config files (parallel)
Task T001: "Create pyproject.toml"
Task T002: "Create langgraph.json"
Task T003: "Create .env.example"

# Group 2: .gitignore (parallel with Group 1 or sequential after)
Task T004: "Create .gitignore"

# Group 3: All content files (parallel, can run alongside Group 1)
Task T005: "Create memory/AGENTS.md"
Task T006: "Create skills/linkedin-post/SKILL.md"
Task T007: "Create skills/twitter-post/SKILL.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Content (T005-T007)
3. Complete Phase 3: Core code (T008-T010)
4. **STOP and VALIDATE**: uv sync works, setup_backend.py uploads to S3, main.py starts CLI
5. Deploy/demo if ready

### Full Delivery

1. Complete MVP (Phases 1-3)
2. Validate US2-US6 manually (no additional code needed)
3. Complete Phase 9: README documentation (T011)
4. Final validation: all 8 success criteria pass

---

## Notes

- This is an example project with 11 files total, not a library
- Most user stories (US2-US6) require no additional code tasks — they are delivered by graph.py's configuration
- The core complexity is in T008 (graph.py) which defines the entire agent
- All content files (AGENTS.md, SKILL.md files) have verbatim or adapted content from langgraph-101
- No automated tests — validation is manual via CLI and LangGraph Studio
