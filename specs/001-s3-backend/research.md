# Research: S3 Backend for deepagents

## R1: Protocol API Changes (deprecated → current)

**Decision**: Use current method names (`ls`, `grep`, `glob`) instead of deprecated (`ls_info`, `grep_raw`, `glob_info`).

**Rationale**: The upstream protocol.py shows these old names are deprecated with `DeprecationWarning` and redirect to the new names. New implementations should target the current API directly. The `read()` method in the reference returns raw strings, but the protocol defines `ReadResult` dataclass — use that.

**Alternatives considered**: Implementing deprecated names for backwards compat — rejected because we're a new package, not upgrading an existing one.

## R2: Utility Reuse from deepagents.backends.utils

**Decision**: Reuse `format_content_with_line_numbers()` and `perform_string_replacement()`.

**Rationale**: These are stable, tested utilities already handling edge cases (line numbering, occurrence validation, replace_all logic). No need to reimplement.

**Alternatives considered**: Vendoring the utilities — rejected to avoid maintenance burden and drift.

## R3: Testing Strategy with moto

**Decision**: Use `moto[s3]` with `@mock_aws` decorator for all S3 tests. Create bucket in test fixture.

**Rationale**: moto provides a complete in-memory S3 implementation. No network calls, fast, deterministic. Well-established pattern in the Python AWS ecosystem.

**Alternatives considered**:
- `unittest.mock` patching boto3 calls directly — rejected because it doesn't validate S3 behavior (e.g., pagination, error codes).
- LocalStack — rejected as too heavy for unit tests.

## R4: ReadResult Construction

**Decision**: `read()` returns `ReadResult(file_data=FileData(content=..., encoding="utf-8", created_at=..., modified_at=...))` on success.

**Rationale**: The protocol defines `ReadResult` with `file_data: FileData | None` and `error: str | None`. S3 `get_object` provides `LastModified` for `modified_at`. For `created_at`, use the same timestamp since S3 doesn't track creation time separately.

**Alternatives considered**: Returning formatted line-numbered content in `file_data.content` — need to verify whether protocol expects raw content or formatted. Based on `FilesystemBackend`, `ReadResult.file_data` contains raw content, and formatting is done by middleware. However, the reference implementation returns formatted content. Will follow the reference pattern since the protocol `read()` docstring says "Read file content with line numbers".

## R5: Logging Approach

**Decision**: Use standard `logging.getLogger(__name__)` at DEBUG level. No colored console output, no custom formatter.

**Rationale**: Library packages should not configure logging — that's the application's responsibility (Python logging best practices). Users can enable debug logging via standard `logging.basicConfig(level=logging.DEBUG)`.

**Alternatives considered**: Keep the reference's colored stderr logging — rejected because it violates library logging conventions and clutters user output.
