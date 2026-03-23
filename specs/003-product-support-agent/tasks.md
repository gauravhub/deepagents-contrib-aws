# Tasks: Product Support Agent Example

**Input**: Design documents from `/specs/003-product-support-agent/`

**Tests**: None — this is an example application validated manually via LangGraph Studio.

## Format: `[ID] [P?] Description`

---

## Phase 1: Setup

<!-- sequential -->
- [x] T001 Create examples/product_support_agent/pyproject.toml with deps: deepagents>=0.4.0, deepagents-contrib-aws>=0.2.0, python-dotenv, langgraph
- [x] T002 Create examples/product_support_agent/.env.example with S3_BACKEND_BUCKET, S3_BACKEND_PREFIX, AGENTCORE_REGION, AWS_REGION/AWS_DEFAULT_REGION

---

## Phase 2: Skills & Memory Content

<!-- parallel-group: 1 (max 3 concurrent) -->
- [x] T003 [P] Create examples/product_support_agent/skills/electronics-support.md — structured skill with diagnostic decision tree for consumer electronics: power issues (won't turn on, random shutdowns), connectivity (WiFi, Bluetooth pairing), display (no picture, flickering, dead pixels), battery drain (fast drain, not charging), audio (no sound, distortion, mic not working). Each symptom → likely cause → step-by-step fix.

- [x] T004 [P] Create examples/product_support_agent/skills/healthcare-products.md — structured skill covering: blood pressure monitors (usage, cuff sizing, calibration, error codes E1-E5), pulse oximeters (proper placement, reading interpretation, low perfusion errors), thermometers (oral/ear/forehead usage, accuracy tips), fitness trackers (heart rate accuracy, step counting issues, sync problems). Include safety disclaimers and "when to consult a professional" guidance.

- [x] T005 [P] Create examples/product_support_agent/skills/finance-products.md — structured skill covering: payment terminals (connection refused, timeout errors, chip reader failures), card readers (pairing, firmware updates), POS systems (transaction reconciliation, end-of-day settlement, voiding transactions), banking apps (login issues, transaction failures). Include security best practices and PCI compliance reminders.

<!-- sequential -->
- [x] T006 Create examples/product_support_agent/memory/AGENTS.md — agent personality file: helpful product support assistant, professional but friendly tone, always ask clarifying questions before diagnosing, include safety disclaimers for healthcare products, remind users about security for financial products, acknowledge limitations honestly.

---

## Phase 3: Core Application

<!-- sequential -->
- [x] T007 Create examples/product_support_agent/graph.py — LangGraph entrypoint: load .env via dotenv, build S3Backend with helper function for prefixed routes, build AgentCoreCodeInterpreterSandbox, create CompositeBackend with sandbox as default and S3 routes for /memories/, /skills/, /conversation_history/, /large_tool_results/. Call create_deep_agent(backend=composite, memory=["/memories/AGENTS.md"], skills=["/skills/"], system_prompt=...). Export compiled graph. Follow the pattern from /home/dhamijag/playground/deep-agents/sdk/hello_world/graph.py.

- [x] T008 Create examples/product_support_agent/setup_backend.py — standalone script: load .env, create S3Backend from env, read local skills/*.md and memory/AGENTS.md files, upload each to S3 at correct paths (e.g., /skills/electronics-support.md, /memories/AGENTS.md). Check if file exists first (read, skip if found). Print status for each file. Runnable via `uv run setup_backend.py`.

---

## Phase 4: Documentation

<!-- sequential -->
- [x] T009 Create examples/product_support_agent/README.md — prerequisites (Python 3.11+, AWS credentials, S3 bucket, AgentCore access), setup steps (cd, cp .env.example .env, edit .env, uv sync, uv run setup_backend.py), run (uv run langgraph dev), what the agent does, skill descriptions, architecture diagram (text).

---

## Dependencies & Execution Order

- **Phase 1**: No dependencies — start immediately
- **Phase 2**: No dependencies on Phase 1 (content files, no imports)
- **Phase 3**: Depends on Phase 1 (pyproject.toml for imports) and Phase 2 (skills/memory for setup_backend reference)
- **Phase 4**: Depends on all prior phases (documents the complete example)

### Parallel Opportunities

- **Phase 2**: T003, T004, T005 can run in parallel (different files, no deps)
