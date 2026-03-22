# Tasks: S3 Backend for deepagents

**Input**: Design documents from `/specs/001-s3-backend/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3, US4)
- Exact file paths included in descriptions

---

## Phase 1: Setup

**Purpose**: Project configuration and dependency setup

<!-- sequential -->
- [x] T001 Update `pyproject.toml` to add `boto3>=1.34.0` and `deepagents` as project dependencies, and `moto[s3]>=5.0` as dev dependency
- [x] T002 Run `uv sync` to install all dependencies and verify no conflicts

---

## Phase 2: Foundation (S3Backend scaffold + path helpers)

**Purpose**: Core class structure and path conversion utilities that all user stories depend on

<!-- sequential -->
- [x] T003 Create `src/deepagents_contrib_aws/s3_backend.py` with S3Backend class skeleton: constructor (`bucket`, `prefix`, `client`, `region_name`), prefix normalization, boto3 client init, `_key()` and `_path()` instance methods, module-level `_path_to_key()` and `_key_to_path()` helpers, and `_map_client_error()` helper. Import all protocol types from `deepagents.backends.protocol` and utilities (`create_file_data`, `format_content_with_line_numbers`, `perform_string_replacement`) from `deepagents.backends.utils`. Use standard `logging.getLogger(__name__)` for logging. Add a `_validate_path()` wrapper that calls path normalization to strip leading `/` and reject `..` traversal sequences before converting to S3 keys.
- [x] T004 Create `from_env()` classmethod on S3Backend reading `S3_BACKEND_BUCKET`, `S3_BACKEND_PREFIX`, `AWS_REGION`/`AWS_DEFAULT_REGION` environment variables. Raise `ValueError` if bucket not provided (constructor-time validation, not a protocol method).
- [x] T005 Update `src/deepagents_contrib_aws/__init__.py` to re-export `S3Backend` from `s3_backend` module. Verify `src/deepagents_contrib_aws/py.typed` marker file exists (already created during project bootstrap).
- [x] T006 Create `tests/conftest.py` with pytest fixtures: `s3_client` (moto mock), `s3_bucket` (creates test bucket), `backend` (S3Backend instance with test bucket and prefix `"test/"`).
- [x] T007 Create `tests/test_helpers.py` with unit tests for `_path_to_key()` and `_key_to_path()` (empty prefix, non-empty prefix, edge cases: root path `/`, trailing slashes, paths with `..`).

---

## Phase 3: User Story 1 — Store and Retrieve Agent Files (P1)

**Story Goal**: Developers can write, read, edit, and list files in S3 via the BackendProtocol interface.
**Independent Test**: Write a file, read it back, edit it, list directory — all return proper result objects.

<!-- sequential -->
- [x] T008 [US1] Implement `ls(path) -> LsResult` in `src/deepagents_contrib_aws/s3_backend.py`: paginated `list_objects_v2` with delimiter `/`, CommonPrefixes as directories, Contents as files with `FileInfo` dicts (`{"path": ..., "is_dir": ..., "size": ..., "modified_at": ...}`), skip self-references, de-duplicate across pages. Return `LsResult(entries=[...])` on success, `LsResult(error=...)` on failure. Design decision: if `list_objects_v2` returns no entries, return `LsResult(entries=[])` — empty directory and non-existent path are indistinguishable in S3.
- [x] T009 [US1] Implement `read(file_path, offset, limit) -> ReadResult` in `src/deepagents_contrib_aws/s3_backend.py`: `get_object`, UTF-8 decode with `errors='replace'`, slice lines by offset/limit, store **raw sliced content** (NOT line-numbered) in `FileData.content`. Use `create_file_data(content=sliced_text, created_at=resp["LastModified"].isoformat())` from `deepagents.backends.utils` to construct FileData dict with proper encoding/timestamps. Return `ReadResult(file_data=...)` on success, `ReadResult(error=...)` on `NoSuchKey`. Note: line-number formatting is applied by middleware, not the backend.
- [x] T010 [US1] Implement `write(file_path, content) -> WriteResult` in `src/deepagents_contrib_aws/s3_backend.py`: `head_object` to check existence (error if exists), then `put_object` with UTF-8 content. Return `WriteResult(path=..., files_update=None)` on success, `WriteResult(error=...)` on failure.
- [x] T011 [US1] Implement `edit(file_path, old_string, new_string, replace_all) -> EditResult` in `src/deepagents_contrib_aws/s3_backend.py`: `get_object`, use `perform_string_replacement()` from `deepagents.backends.utils`, then `put_object`. Note: `perform_string_replacement` returns `tuple[str, int]` on success or `str` on error — if result is a string (error message), return `EditResult(error=result)`. Return `EditResult(path=..., files_update=None, occurrences=N)` on success, `EditResult(error=...)` on failure.

<!-- parallel-group: 1 (max 3 concurrent) -->
- [x] T012 [P] [US1] Create `tests/test_ls.py` with tests for `ls()`: list files and dirs, empty directory, nested directories, pagination (>1000 objects), error handling.
- [x] T013 [P] [US1] Create `tests/test_read.py` with tests for `read()`: happy path, offset/limit pagination, file not found, binary content (UTF-8 replace), empty file.
- [x] T014 [P] [US1] Create `tests/test_write.py` with tests for `write()`: create new file, file already exists error, empty content, S3 permission error.

<!-- sequential -->
- [x] T015 [US1] Create `tests/test_edit.py` with tests for `edit()`: single occurrence, multiple occurrences with `replace_all=True`, zero occurrences error, multiple occurrences with `replace_all=False` error, file not found.

---

## Phase 4: User Story 2 — Search Agent Workspace Files (P2)

**Story Goal**: Developers can search files by name pattern (glob) and content (grep).
**Independent Test**: Upload files, glob for `*.py`, grep for a string — both return proper result objects.

<!-- sequential (T016/T017 both modify s3_backend.py — cannot parallelize) -->
- [x] T016 [US2] Implement `grep(pattern, path, glob) -> GrepResult` in `src/deepagents_contrib_aws/s3_backend.py`: paginated `list_objects_v2`, filter by glob using `fnmatch.fnmatch(path.lstrip("/"), glob_pattern)` (strip leading `/` before matching), skip files >10MB (10 * 1024 * 1024 bytes), literal substring search per line, return `GrepResult(matches=[GrepMatch(...)])` on success.
- [x] T017 [US2] Implement `glob(pattern, path) -> GlobResult` in `src/deepagents_contrib_aws/s3_backend.py`: paginated `list_objects_v2`, filter using `fnmatch.fnmatch(virtual_path.lstrip("/"), pattern)` (strip leading `/` before matching to handle patterns like `*.py`), return `GlobResult(matches=[FileInfo(...)])` on success.

<!-- parallel-group: 2 (max 2 concurrent) -->
- [x] T018 [P] [US2] Create `tests/test_grep.py` with tests for `grep()`: literal match, no matches, glob filter, skip large files (>10MB), search in subdirectory, error handling.
- [x] T019 [P] [US2] Create `tests/test_glob.py` with tests for `glob()`: wildcard match `*.py`, recursive `**/*.py`, no matches returns empty, base path filtering.

---

## Phase 5: User Story 3 — Bulk File Transfer (P2)

**Story Goal**: Developers can upload and download multiple files in a single call with per-file error handling.
**Independent Test**: Upload batch of files, download them back (including one missing) — verify partial success.

<!-- sequential (T020/T021 both modify s3_backend.py — cannot parallelize) -->
- [x] T020 [US3] Implement `upload_files(files) -> list[FileUploadResponse]` in `src/deepagents_contrib_aws/s3_backend.py`: iterate file list, `put_object` each, map `ClientError` to `FileOperationError` codes via `_map_client_error()`, return responses in same order as input.
- [x] T021 [US3] Implement `download_files(paths) -> list[FileDownloadResponse]` in `src/deepagents_contrib_aws/s3_backend.py`: iterate paths, `get_object` each, map `ClientError` codes via `_map_client_error()` (`NoSuchKey` → `file_not_found`, `AccessDenied` → `permission_denied`), handle zero-length files, return responses in same order.

<!-- sequential -->
- [x] T022 [US3] Create `tests/test_bulk.py` with tests for `upload_files()` and `download_files()`: happy path batch, partial failure (one missing file), permission error mapping, empty input list, order preservation.

---

## Phase 6: User Story 4 — Environment Configuration (P3)

**Story Goal**: Developers can configure S3Backend via environment variables.
**Independent Test**: Set env vars, call `from_env()`, verify backend instance configuration.

<!-- sequential -->
- [x] T023 [US4] Create `tests/test_from_env.py` with tests for `from_env()`: all env vars set, missing bucket raises ValueError, prefix defaults to empty, region from `AWS_REGION`, region from `AWS_DEFAULT_REGION`, constructor params override env vars.

---

## Phase 7: Polish & Cross-Cutting

**Purpose**: Code quality, linting, final validation

<!-- sequential -->
- [x] T024 Run `uv run ruff check src/ tests/` and fix any linting issues
- [x] T025 Run `uv run pytest` to verify all tests pass
- [x] T026 Run `uv build` to verify the package builds correctly

---

## Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundation) → Phase 3 (US1: Core File Ops)
                                        → Phase 4 (US2: Search) [can start after Phase 2]
                                        → Phase 5 (US3: Bulk Transfer) [can start after Phase 2]
                                        → Phase 6 (US4: Env Config) [can start after Phase 2]
Phase 3-6 → Phase 7 (Polish)
```

User stories 1-4 can be implemented in parallel after Phase 2 completes, though US1 (P1) is recommended first as MVP.

## Implementation Strategy

1. **MVP**: Phases 1-3 (Setup + Foundation + US1) — delivers core file operations
2. **Increment 2**: Phases 4-5 (US2 + US3) — adds search and bulk transfer
3. **Increment 3**: Phase 6 (US4) — adds environment configuration
4. **Final**: Phase 7 — polish and validation

## Summary

| Phase | Story | Tasks | Parallel Opportunities |
|-------|-------|-------|----------------------|
| 1. Setup | — | 2 | None (sequential) |
| 2. Foundation | — | 5 | None (sequential) |
| 3. US1: Core File Ops | P1 | 8 | T012/T013/T014 (parallel-group 1) |
| 4. US2: Search | P2 | 4 | T018/T019 (parallel-group 2) |
| 5. US3: Bulk Transfer | P2 | 3 | None (sequential — same file) |
| 6. US4: Env Config | P3 | 1 | None |
| 7. Polish | — | 3 | None (sequential) |
| **Total** | | **26** | **2 parallel groups** |
