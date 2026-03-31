# Deep Research Agent — Demo Script

Step-by-step prompts to showcase agent features in LangSmith Studio.
Run each prompt in order. Start a **new thread** where indicated.

> **Setup:** Pass `user_id` in the config panel: `{"user_id": "alice"}`

---

## 1. Basic Conversation

Show the agent understands its role without using any tools.

```
What can you help me with? List your capabilities briefly.
```

---

## 2. Web Research (Tavily Search)

Trigger a direct web search using the Tavily tool.

```
What is Amazon Bedrock AgentCore? Give me a brief summary.
```

---

## 3. Research Subagent Delegation

The agent delegates to its research subagent for deeper multi-step research.

```
Delegate to your research agent: Research the latest trends in AI agent frameworks in 2025. Focus on LangGraph, CrewAI, and AutoGen.
```

---

## 4. Code Execution (AgentCore Sandbox)

Demonstrate the AgentCore Code Interpreter sandbox.

```
Write and run a Python script that generates 10 random numbers, calculates the mean and standard deviation, then prints the results.
```

---

## 5. Human-in-the-Loop (File Write Approval)

The agent will pause and ask for approval before writing a file.
**Click "Approve" when prompted.**

```
Create a file called /report_draft.md with a short summary of what we've discussed so far.
```

---

## 6. Semantic Memory — Private (User Scope)

Save a personal preference to Alice's private semantic memory.

```
Remember this about me: I prefer dark mode, use Python primarily, and work on the AI platform team. Save it to my private semantic memory.
```

---

## 7. Semantic Memory — Shared

Save a team-wide fact to shared semantic memory.

```
Save this to shared semantic memory: Our project uses Amazon S3 for storage, Bedrock for model inference, and AgentCore for code execution sandboxes.
```

---

## 8. Procedural Memory — Shared

Save a team standard that all users should follow.

```
Save this team rule to shared procedural memory: All reports must include an executive summary, numbered findings, and a sources section with URLs.
```

---

## 9. Procedural Memory — Private (User Scope)

Save a personal workflow preference.

```
Save to my private procedural memory: I prefer bullet points over paragraphs, and I like code examples included inline.
```

---

## 10. Episodic Memory — Private Session Log

Ask the agent to log this demo session.

```
Save an episodic session log for today's demo. Include what we covered: web research, code execution, and memory setup. Save it to my private episodic memory with today's date in the filename.
```

---

## 11. Memory Recall — Same User

Verify Alice can recall all her memories.

> **Start a new thread** (keep `user_id: alice`)

```
Check all my memory paths and tell me what you know about me, what team standards exist, and what past sessions are logged.
```

---

## 12. Memory Isolation — Different User

Switch to Bob and show he can see shared but NOT Alice's private memories.

> **Start a new thread** with config: `{"user_id": "bob"}`

```
List everything in all six memory paths. Tell me what you can and cannot see.
```

**Expected:** Bob sees shared semantic, procedural, and episodic files but has
empty user/ folders (no access to Alice's private data).

---

## 13. Bob Adds His Own Private Memory

Show that Bob's private memory is isolated from Alice's.

```
Save to my private semantic memory: Bob prefers light mode and works on the infrastructure team.
```

---

## 14. Cross-User Verification

Confirm both users have isolated private memories.

> **Start a new thread** with config: `{"user_id": "alice"}`

```
Check /memories/semantic/user/ — what personal preferences do you have stored for me?
```

**Expected:** Alice sees her own preferences (dark mode, Python) but NOT Bob's.

---

## 15. Research with Memory Context

Show the agent uses stored memory to personalize research.

```
Based on what you know about our project stack from shared memory, research best practices for securing S3 buckets used with AI agent frameworks. Format the output following our team report standards from procedural memory.
```

**Expected:** The agent reads shared semantic memory (project stack) and shared
procedural memory (report format) before researching, then produces a report
following the stored standards.

---

## Demo Summary

| # | Feature | Key Takeaway |
|---|---------|-------------|
| 1-2 | Basic + Search | Agent uses Tavily for web research |
| 3 | Subagent | Delegates complex research to specialist |
| 4 | Code Execution | Runs Python in AgentCore sandbox |
| 5 | HITL | File writes require human approval |
| 6-10 | Memory Write | 3 categories x 2 scopes = 6 memory paths |
| 11 | Memory Recall | Persistent across threads for same user |
| 12-14 | Isolation | user/ is private; shared/ is global |
| 15 | Memory + Research | Agent combines memory context with live research |
