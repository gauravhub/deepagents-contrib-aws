# Quickstart: S3 Backend for deepagents

## Installation

```bash
pip install deepagents-contrib-aws
```

## Usage

### From constructor

```python
from deepagents_contrib_aws import S3Backend

backend = S3Backend(bucket="my-bucket", prefix="agent/workspace/")
```

### From environment variables

```bash
export S3_BACKEND_BUCKET=my-bucket
export S3_BACKEND_PREFIX=agent/workspace/
export AWS_REGION=us-west-2
```

```python
from deepagents_contrib_aws import S3Backend

backend = S3Backend.from_env()
```

### With deepagents

```python
from deepagents import create_deep_agent
from deepagents_contrib_aws import S3Backend

backend = S3Backend.from_env()
agent = create_deep_agent(backend=backend)
```

### Basic operations

```python
backend = S3Backend(bucket="my-bucket", prefix="demo/")

# Write a file
result = backend.write("/hello.py", "print('hello')")

# Read it back
result = backend.read("/hello.py")

# Edit it
result = backend.edit("/hello.py", "hello", "world")

# List directory
result = backend.ls("/")

# Search
result = backend.grep("world", path="/")
result = backend.glob("*.py")
```
