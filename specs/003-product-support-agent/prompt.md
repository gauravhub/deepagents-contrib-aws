# Product Support Agent Example

## Feature Description

Build a fully self-contained example of a product support deep agent in examples/product_support_agent/. This example has its own pyproject.toml and uv environment — completely independent from the parent project.

The agent uses the deepagents framework with deepagents-contrib-aws backends:

- **Default backend**: AgentCoreCodeInterpreterSandbox from deepagents-contrib-aws for code execution
- **S3 routing via CompositeBackend**: Route these paths to S3Backend:
  - /memories/ — persistent agent memory (AGENTS.md)
  - /skills/ — skill library files
  - /conversation_history/ — conversation transcripts
  - /large_tool_results/ — overflow storage for large tool outputs

The agent is a product support assistant with 3 skills stored as markdown files in S3:

1. **electronics-support** — Troubleshoot consumer electronics (TVs, laptops, smartphones, headphones). Decision tree: symptom → cause → fix. Covers power, connectivity, display, battery, audio issues.

2. **healthcare-products** — Usage guidance and troubleshooting for healthcare/wellness devices (BP monitors, pulse oximeters, thermometers, fitness trackers). Proper usage, calibration, error codes.

3. **finance-products** — Help with financial product issues (banking apps, payment terminals, card readers, POS systems). Transaction errors, connectivity, reconciliation, security best practices.

## Structure

```
examples/product_support_agent/
├── pyproject.toml
├── .env.example
├── README.md
├── graph.py
├── setup_backend.py
├── skills/
│   ├── electronics-support.md
│   ├── healthcare-products.md
│   └── finance-products.md
└── memory/
    └── AGENTS.md
```
