# Quickstart: AgentCore Code Interpreter Sandbox

## Installation

```bash
pip install deepagents-contrib-aws[agentcore]
```

## Basic Usage

### From constructor

```python
from deepagents_contrib_aws import AgentCoreCodeInterpreterSandbox

sandbox = AgentCoreCodeInterpreterSandbox(region_name="us-west-2")

# Execute Python (state preserved across calls)
result = sandbox.execute('python3 -c "x = 42; print(x)"')
print(result.output)  # "42"

# Execute shell commands
result = sandbox.execute("echo hello && ls /tmp")
print(result.output)

# Clean up
sandbox.stop()
```

### With context manager

```python
from deepagents_contrib_aws import AgentCoreCodeInterpreterSandbox

with AgentCoreCodeInterpreterSandbox() as sandbox:
    result = sandbox.execute('python3 -c "print(1 + 1)"')
    print(result.output)  # "2"
# Session automatically cleaned up
```

### From environment variables

```bash
export AGENTCORE_REGION=us-west-2
export AGENTCORE_SESSION_TIMEOUT=1800
```

```python
from deepagents_contrib_aws import AgentCoreCodeInterpreterSandbox

sandbox = AgentCoreCodeInterpreterSandbox.from_env()
```

### File operations

```python
with AgentCoreCodeInterpreterSandbox() as sandbox:
    # Upload files
    sandbox.upload_files([
        ("/tmp/data.csv", b"name,value\nfoo,42"),
        ("/tmp/image.png", open("local.png", "rb").read()),
    ])

    # Download files
    results = sandbox.download_files(["/tmp/data.csv"])
    print(results[0].content)  # b"name,value\nfoo,42"
```

### With deepagents

```python
from deepagents import create_deep_agent
from deepagents_contrib_aws import AgentCoreCodeInterpreterSandbox

sandbox = AgentCoreCodeInterpreterSandbox.from_env()
agent = create_deep_agent(backend=sandbox)
```
