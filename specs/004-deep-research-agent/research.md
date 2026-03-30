# Research: Deep Research Agent Example

**Date**: 2026-03-30

## R1: CompositeBackend Route Pattern for Structured Memory

**Decision**: Use 7 S3Backend routes in CompositeBackend with longest-prefix matching. Three sub-routes under `/memories/` (semantic, episodic, procedural) each get their own S3 prefix, plus a parent `/memories/` route for AGENTS.md.

**Rationale**: CompositeBackend uses longest-prefix matching, so `/memories/semantic/` takes priority over `/memories/`. This is confirmed by the deepagents notebook (Cell 69-72) and the existing `product_support_agent/graph.py` pattern. Each route gets its own `_s3()` call with a distinct suffix.

**Alternatives considered**:
- Single `/memories/` route: Rejected because it doesn't separate memory types into distinct S3 prefixes.
- StoreBackend for memories (langgraph-101 pattern): Rejected because the spec requires S3-backed persistence, not LangGraph Store.

## R2: graph.py Pattern Alignment with product_support_agent

**Decision**: Follow the exact `_build_backend()` / `_s3()` helper pattern from `product_support_agent/graph.py` (lines 49-102), adding 3 extra routes for structured memory sub-types.

**Rationale**: Consistency across examples reduces learning curve. The pattern handles env var validation, prefix normalization, and S3Backend construction cleanly.

**Alternatives considered**:
- `from_env()` class method on S3Backend: Rejected because the helper pattern gives more control over prefix construction per route.

## R3: Research Subagent Definition

**Decision**: Define the research subagent as a Python dict inline in `graph.py` (not a separate file), matching the langgraph-101 pattern. Include current date injection, hard limits on search calls, and structured output format.

**Rationale**: The deepagents framework accepts subagents as dicts with name, description, system_prompt, and tools keys. This is the simplest approach and matches the reference implementation.

**Alternatives considered**:
- Separate subagent file: Rejected because the spec explicitly says "NOT a separate file."
- Full agent class: Overkill for a dict-based subagent definition.

## R4: Skills Content Source

**Decision**: Copy skills verbatim from `/tmp/langgraph-101/agents/deep_agent/skills/` (linkedin-post/SKILL.md and twitter-post/SKILL.md).

**Rationale**: The spec says "Copy the exact content from langgraph-101." These files are already well-structured with YAML frontmatter, format instructions, tone guidelines, and examples.

**Alternatives considered**: None -- spec is explicit about copying.

## R5: HITL in CLI Mode

**Decision**: In CLI mode (main.py), HITL interrupts are not surfaced to the user because the simple `graph.invoke()` pattern doesn't handle interrupt state. HITL is fully functional in LangGraph Studio. The README should document this distinction.

**Rationale**: The product_support_agent/main.py uses the same simple invoke pattern without interrupt handling. Adding interrupt handling to the CLI would require a more complex event loop that's beyond the scope of this example.

**Alternatives considered**:
- Full interrupt handling in CLI: Rejected as over-engineering for an example project. LangGraph Studio is the intended HITL interface.
