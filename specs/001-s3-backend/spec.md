# Feature Specification: S3 Backend for deepagents

**Feature Branch**: `001-s3-backend`
**Created**: 2026-03-20
**Status**: Draft
**Input**: User description: "Implement an S3-based backend for the deepagents framework by implementing the BackendProtocol interface"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Store and Retrieve Agent Files in S3 (Priority: P1)

A developer using the deepagents framework wants to persist agent workspace files (code, config, documents) in Amazon S3 so that files survive across agent sessions, are accessible from multiple environments, and benefit from S3's durability and availability.

**Why this priority**: This is the core value proposition — without reliable file storage and retrieval, no other feature matters. It covers the fundamental `read`, `write`, `ls`, and `edit` operations that every agent session relies on.

**Independent Test**: Can be fully tested by creating an S3Backend instance, writing a file, reading it back, listing directory contents, and editing file content. Delivers persistent, durable file storage for agent workspaces.

**Acceptance Scenarios**:

1. **Given** an S3Backend configured with a bucket and prefix, **When** a developer writes a file at `/workspace/hello.py` with content `print("hello")`, **Then** the file is stored in S3 at the correct key and a successful WriteResult is returned.
2. **Given** a file exists at `/workspace/hello.py`, **When** a developer reads it with default offset and limit, **Then** the file content is returned in a ReadResult with correct line-numbered content.
3. **Given** a file exists at `/workspace/hello.py`, **When** a developer edits it replacing `"hello"` with `"world"`, **Then** the file is updated in S3 and an EditResult is returned with occurrences count of 1.
4. **Given** multiple files exist under `/workspace/`, **When** a developer lists the `/workspace/` directory, **Then** an LsResult is returned containing FileInfo entries for each file and subdirectory with size and modification timestamps.
5. **Given** a file already exists at `/workspace/hello.py`, **When** a developer attempts to write a new file at the same path, **Then** a WriteResult with an error is returned (no overwrite).

---

### User Story 2 - Search Agent Workspace Files (Priority: P2)

A developer wants to search for files by name patterns (glob) and search file contents for specific text (grep) across the S3-backed workspace, enabling agents to locate relevant files efficiently.

**Why this priority**: Search is essential for agents navigating large workspaces but depends on basic file operations being functional first.

**Independent Test**: Can be tested by uploading several files to S3, then running glob to find files by pattern and grep to search content. Delivers workspace-wide file discovery.

**Acceptance Scenarios**:

1. **Given** files exist at `/src/main.py`, `/src/utils.py`, and `/docs/readme.md`, **When** a developer runs glob with pattern `*.py`, **Then** a GlobResult is returned containing FileInfo for both `.py` files.
2. **Given** a file at `/src/main.py` contains the text `import boto3`, **When** a developer runs grep with pattern `boto3`, **Then** a GrepResult is returned with a match entry showing the file path, line number, and matching text.
3. **Given** a file larger than 10MB exists in the workspace, **When** a developer runs grep, **Then** the large file is skipped without error.

---

### User Story 3 - Bulk File Transfer (Priority: P2)

A developer wants to upload and download multiple files in a single operation, enabling efficient batch transfers between local environments and the S3-backed workspace.

**Why this priority**: Batch operations are critical for initial workspace setup and result retrieval but build on the same S3 primitives as Story 1.

**Independent Test**: Can be tested by uploading a batch of files and then downloading them back, verifying content integrity. Delivers efficient multi-file transfer.

**Acceptance Scenarios**:

1. **Given** three files to upload, **When** a developer calls upload_files with the file list, **Then** all files are stored in S3 and a list of FileUploadResponse objects is returned, one per file, in the same order.
2. **Given** two files exist and one does not, **When** a developer calls download_files for all three paths, **Then** two FileDownloadResponse objects contain the file content and one contains a `file_not_found` error.

---

### User Story 4 - Configure S3 Backend from Environment (Priority: P3)

A developer wants to configure the S3Backend using environment variables so that credentials and bucket configuration can be managed externally (e.g., in CI/CD, container orchestration, or IAM roles) without hardcoding.

**Why this priority**: Environment-based configuration is important for production deployment but is a convenience layer on top of the core functionality.

**Independent Test**: Can be tested by setting environment variables and calling `S3Backend.from_env()`, verifying the returned instance has the correct bucket, prefix, and region.

**Acceptance Scenarios**:

1. **Given** `S3_BACKEND_BUCKET=my-bucket` and `S3_BACKEND_PREFIX=agent/workspace/` are set, **When** a developer calls `S3Backend.from_env()`, **Then** an S3Backend instance is returned configured for that bucket and prefix.
2. **Given** `S3_BACKEND_BUCKET` is not set, **When** a developer calls `S3Backend.from_env()`, **Then** a clear error is raised indicating the required environment variable is missing.
3. **Given** `AWS_REGION=us-west-2` is set, **When** a developer calls `S3Backend.from_env()`, **Then** the backend is configured for the `us-west-2` region.

---

### Edge Cases

- What happens when reading a binary (non-UTF-8) file? The system gracefully decodes with replacement characters.
- What happens when the S3 bucket does not exist or is inaccessible? Appropriate error codes are returned in result objects (`permission_denied`).
- What happens when editing a file and the `old_string` appears zero times? An error is returned indicating no match found.
- What happens when editing a file and the `old_string` appears multiple times but `replace_all` is False? An error is returned indicating ambiguous match.
- What happens when the S3 key prefix has leading/trailing slashes? The prefix is normalized consistently regardless of how the user provides it.
- What happens when a path contains `..` or other traversal sequences? Paths are normalized to prevent unintended key construction.

## Clarifications

### Session 2026-03-20

- No critical ambiguities detected. The upstream BackendProtocol interface contract and the existing reference implementation (`/home/dhamijag/playground/deep-agents/sdk/hello_world/s3_backend.py`) resolve all design questions. Spec is ready for planning.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement all eight BackendProtocol methods: `ls`, `read`, `write`, `edit`, `grep`, `glob`, `upload_files`, `download_files`.
- **FR-002**: System MUST return protocol-defined result objects (ReadResult, WriteResult, EditResult, LsResult, GrepResult, GlobResult, FileUploadResponse, FileDownloadResponse) for all operations.
- **FR-003**: System MUST map S3/AWS errors to standardized FileOperationError codes: `file_not_found`, `permission_denied`, `is_directory`, `invalid_path`.
- **FR-004**: System MUST never raise exceptions to callers — all errors are returned in result objects.
- **FR-005**: System MUST support configuring the backend via constructor parameters: bucket name, key prefix, optional pre-configured S3 client, optional region.
- **FR-006**: System MUST provide a `from_env()` classmethod that reads configuration from environment variables (`S3_BACKEND_BUCKET`, `S3_BACKEND_PREFIX`, `AWS_REGION` or `AWS_DEFAULT_REGION`).
- **FR-007**: System MUST normalize the key prefix to ensure consistent path-to-key mapping regardless of trailing slash presence.
- **FR-008**: The `write` method MUST prevent overwriting existing files — it returns an error if the file already exists.
- **FR-009**: The `edit` method MUST validate string replacement occurrences — exactly one match required unless `replace_all` is True.
- **FR-010**: The `read` method MUST support line-based pagination via `offset` and `limit` parameters.
- **FR-011**: The `grep` method MUST perform literal text search (not regex) and skip files larger than 10MB.
- **FR-012**: The `glob` method MUST filter files using shell-style wildcard patterns.
- **FR-013**: System MUST handle binary files gracefully by decoding with UTF-8 `errors='replace'`.
- **FR-014**: Batch operations (`upload_files`, `download_files`) MUST support partial success — individual file failures do not fail the entire batch.
- **FR-015**: System MUST be installable as a standalone PyPI package with `boto3` and `deepagents` as dependencies.

### Key Entities

- **S3Backend**: The primary class implementing BackendProtocol. Configured with a bucket name and optional key prefix. Translates virtual file paths to S3 object keys.
- **Virtual Path**: An absolute path (e.g., `/workspace/file.py`) used by the deepagents framework. Mapped to S3 keys using the configured prefix.
- **S3 Key**: The actual object key in S3, composed of prefix + virtual path (e.g., `agent/workspace/file.py`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All eight BackendProtocol methods pass unit tests covering both happy path and error scenarios.
- **SC-002**: The package installs cleanly via `pip install` with no dependency conflicts against deepagents and boto3.
- **SC-003**: Developers can configure the backend with a single `from_env()` call using standard AWS environment variables.
- **SC-004**: All S3 API errors are translated to protocol-standard error codes — no raw AWS exceptions leak to callers.
- **SC-005**: The package passes ruff linting with the project's configured rules and has type hints on all public methods.
