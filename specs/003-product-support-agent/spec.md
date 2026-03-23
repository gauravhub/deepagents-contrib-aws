# Feature Specification: Product Support Agent Example

**Feature Branch**: `feature/product-support-agent`
**Created**: 2026-03-22
**Status**: Draft
**Input**: User description: "Build a self-contained product support deep agent example using deepagents with deepagents-contrib-aws backends"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run the Product Support Agent (Priority: P1)

A developer wants to clone the repo, navigate to the example directory, configure AWS credentials, and launch a working product support agent. The agent uses AgentCore Code Interpreter for code execution and S3 for persistent storage of memories, skills, and conversation history.

**Why this priority**: This is the core purpose of the example — a developer must be able to set up and run the agent end-to-end. Without this, the example has no value.

**Independent Test**: Can be tested by running `cd examples/product_support_agent && uv sync && uv run setup_backend.py && uv run langgraph dev` and interacting with the agent in LangGraph Studio.

**Acceptance Scenarios**:

1. **Given** a developer with AWS credentials and an S3 bucket, **When** they run `uv sync` in the example directory, **Then** all dependencies are installed in an isolated venv with no connection to the parent project.
2. **Given** a configured `.env` file, **When** the developer runs `uv run setup_backend.py`, **Then** the 3 skill files and AGENTS.md memory file are uploaded to S3 at the correct paths.
3. **Given** the backend is set up, **When** the developer runs `uv run langgraph dev`, **Then** the agent starts and is accessible via LangGraph Studio.
4. **Given** a running agent, **When** a user asks "My laptop won't turn on", **Then** the agent invokes the electronics-support skill and walks through the diagnostic tree.

---

### User Story 2 - Electronics Product Support (Priority: P1)

A user asks the agent for help troubleshooting a consumer electronics device. The agent uses the electronics-support skill to identify the symptom category, walk through a diagnostic decision tree, and provide step-by-step fix instructions.

**Why this priority**: This is the primary demonstration of skill-based support. Electronics troubleshooting has clear decision trees that showcase the agent's ability to follow structured workflows.

**Independent Test**: Ask the agent about a power issue with a laptop and verify it walks through the correct diagnostic steps.

**Acceptance Scenarios**:

1. **Given** a user reports "my TV has no picture", **When** the agent processes the request, **Then** it identifies this as a display issue and provides relevant troubleshooting steps.
2. **Given** a user reports "my headphones won't connect to Bluetooth", **When** the agent processes the request, **Then** it identifies this as a connectivity issue and provides pairing/reset instructions.
3. **Given** a symptom that doesn't match any category, **When** the agent processes the request, **Then** it asks clarifying questions to narrow down the issue.

---

### User Story 3 - Healthcare Product Support (Priority: P2)

A user asks for help with a healthcare or wellness device. The agent uses the healthcare-products skill to provide usage guidance, calibration instructions, error code resolution, and safety information.

**Why this priority**: Healthcare devices require careful guidance including safety disclaimers. This demonstrates the agent handling domain-specific concerns like "when to seek professional help."

**Independent Test**: Ask the agent about a blood pressure monitor error code and verify it provides the correct resolution with appropriate safety disclaimers.

**Acceptance Scenarios**:

1. **Given** a user asks "how do I calibrate my blood pressure monitor", **When** the agent processes the request, **Then** it provides step-by-step calibration instructions from the healthcare-products skill.
2. **Given** a user reports an error code from a pulse oximeter, **When** the agent processes the request, **Then** it looks up the error code and provides the resolution.
3. **Given** a user describes symptoms suggesting a medical concern, **When** the agent processes the request, **Then** it provides the device troubleshooting but includes a disclaimer to consult a healthcare professional.

---

### User Story 4 - Finance Product Support (Priority: P2)

A user asks for help with a financial product or device. The agent uses the finance-products skill to troubleshoot transaction errors, connectivity issues, and provide security best practices.

**Why this priority**: Financial products involve security-sensitive operations. This demonstrates the agent providing structured troubleshooting for payment processing while emphasizing security practices.

**Independent Test**: Ask the agent about a payment terminal connection error and verify it provides the correct troubleshooting flow.

**Acceptance Scenarios**:

1. **Given** a user reports "my payment terminal shows 'connection refused'", **When** the agent processes the request, **Then** it walks through the connectivity troubleshooting flow from the finance-products skill.
2. **Given** a user asks about PCI compliance for their card reader, **When** the agent processes the request, **Then** it provides security best practices from the skill.
3. **Given** a user reports a transaction reconciliation discrepancy, **When** the agent processes the request, **Then** it guides them through the reconciliation troubleshooting steps.

---

### User Story 5 - Persistent Memory and Conversation History (Priority: P3)

The agent maintains persistent memory (AGENTS.md) loaded from S3 at startup, and conversation history is automatically stored in S3. This allows the agent to maintain context across sessions and follow consistent behavior patterns defined in its memory file.

**Why this priority**: Persistence is important for production agents but secondary to core skill-based support. The deepagents framework handles this via CompositeBackend routing — the example demonstrates the pattern.

**Independent Test**: Start the agent, have a conversation, restart it, and verify it can reference its memory file for personality/behavior guidelines.

**Acceptance Scenarios**:

1. **Given** AGENTS.md is uploaded to /memories/, **When** the agent starts, **Then** it loads the memory file and follows the personality and behavior guidelines defined in it.
2. **Given** a conversation in progress, **When** the agent generates responses, **Then** conversation history is automatically persisted to /conversation_history/ in S3.
3. **Given** a tool produces output exceeding the token limit, **When** the middleware processes it, **Then** the large output is stored at /large_tool_results/ in S3.

---

### Edge Cases

- What happens when S3 bucket is not configured? The setup_backend.py script should fail with a clear error message explaining what to configure.
- What happens when AgentCore region is not set? graph.py should fail with a clear error rather than silently using a wrong default.
- What happens when skills are not uploaded to S3? The agent starts but has no skills — it should still respond helpfully and suggest running setup_backend.py.
- What happens when AWS credentials are missing or expired? The agent should surface a clear error at startup, not during a user conversation.
- What happens when the user asks about a product category not covered by any skill? The agent should acknowledge it doesn't have a specific skill for that category and provide general troubleshooting guidance.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The example MUST be fully self-contained in `examples/product_support_agent/` with its own `pyproject.toml` and isolated uv environment.
- **FR-002**: The example MUST use `CompositeBackend` with `AgentCoreCodeInterpreterSandbox` as the default backend and `S3Backend` for routing `/memories/`, `/skills/`, `/conversation_history/`, and `/large_tool_results/`.
- **FR-003**: The `graph.py` MUST export a compiled `StateGraph` compatible with LangGraph Studio (`uv run langgraph dev`).
- **FR-004**: The `setup_backend.py` MUST upload local `skills/*.md` and `memory/AGENTS.md` files to S3 at the correct paths, idempotently (skip if file already exists).
- **FR-005**: The example MUST include 3 skill files: `electronics-support.md`, `healthcare-products.md`, `finance-products.md`.
- **FR-006**: Each skill MUST follow the deepagents skill format — a structured markdown file with instructions the agent can follow.
- **FR-007**: The `electronics-support` skill MUST include a diagnostic decision tree covering: power issues, connectivity, display, battery drain, and audio problems.
- **FR-008**: The `healthcare-products` skill MUST include usage instructions, calibration steps, error codes, and safety disclaimers.
- **FR-009**: The `finance-products` skill MUST include transaction error troubleshooting, connectivity setup, reconciliation guidance, and security best practices.
- **FR-010**: The `AGENTS.md` memory file MUST define the agent's personality as a helpful product support assistant and include behavior guidelines.
- **FR-011**: The `pyproject.toml` MUST declare `deepagents>=0.4.0`, `deepagents-contrib-aws>=0.2.0`, `python-dotenv`, and `langgraph` as dependencies.
- **FR-012**: The example MUST include a `.env.example` file documenting all required environment variables.
- **FR-013**: The example MUST include a `README.md` with setup prerequisites, installation steps, and how to run.
- **FR-014**: The `setup_backend.py` MUST be runnable standalone via `uv run setup_backend.py`.

### Key Entities

- **Product Support Agent**: A deepagents-powered agent that uses skills to help users troubleshoot products across electronics, healthcare, and finance categories.
- **CompositeBackend**: Routes file storage paths to S3 while defaulting code execution to AgentCore.
- **Skills**: Structured markdown files stored in S3 that the agent reads and follows for domain-specific troubleshooting.
- **AGENTS.md**: Memory file defining the agent's personality and behavior guidelines.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can set up and launch the agent in under 5 minutes following the README instructions.
- **SC-002**: The agent correctly invokes the appropriate skill when asked about electronics, healthcare, or finance products.
- **SC-003**: The `setup_backend.py` script successfully uploads all skill and memory files to S3 without errors.
- **SC-004**: The example runs with a completely isolated dependency environment — no imports or venv sharing with the parent project.
- **SC-005**: The agent provides structured, step-by-step troubleshooting guidance (not generic responses) when a skill matches the user's query.

## Clarifications

### Session 2026-03-22

- No critical ambiguities detected. Feature description is comprehensive.
- Skill format follows deepagents conventions (structured markdown with instructions).
- CompositeBackend routing pattern matches existing reference in sdk/hello_world/graph.py.

## Assumptions

- The developer has AWS credentials configured with permissions for both S3 and AgentCore Code Interpreter.
- The `deepagents>=0.4.0` package provides `create_deep_agent`, `CompositeBackend`, and skill/memory loading from backend paths.
- The `deepagents-contrib-aws>=0.2.0` package is published on PyPI with both `S3Backend` and `AgentCoreCodeInterpreterSandbox`.
- LangGraph is compatible with the agent graph exported by `create_deep_agent`.
