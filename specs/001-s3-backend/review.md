# Pre-Implementation Review

**Feature**: S3 Backend for deepagents
**Artifacts reviewed**: spec.md, plan.md, tasks.md, checklists/protocol-compliance.md, research.md, data-model.md
**Review model**: Claude Sonnet 4.6
**Generating model**: Claude Opus 4.6

## Summary

| Dimension | Verdict | Issues |
|-----------|---------|--------|
| Spec-Plan Alignment | PASS | All 4 user stories and all FRs are addressed |
| Plan-Tasks Completeness | WARN | `create_file_data` utility missed |
| Dependency Ordering | PASS | Phase ordering correct; no forward references |
| Parallelization Correctness | WARN | T016/T017 both write to `s3_backend.py` — same-file conflict |
| Feasibility & Risk | FAIL | `read()` FileData construction under-specified; `format_content_with_line_numbers` usage unclear |
| Standards Compliance | WARN | `validate_path()` utility exists but not wired into any task |
| Implementation Readiness | WARN | T009 instruction for FileData incomplete; TypedDict construction syntax |

**Overall**: READY WITH WARNINGS (one FAIL-level finding must be resolved before T009 implementation)

## Findings

### Critical (FAIL — must fix before implementing)

**F1: `read()` content in `FileData` must be raw, not line-numbered — plan contradicts itself**

T009 instructs using `format_content_with_line_numbers()` inside `read()` and storing in `FileData.content`. This is wrong:
- `utils.py` has `slice_read_response()` for raw text windows; line-number formatting is applied by middleware
- `create_file_data()` utility is the canonical way to build FileData — neither plan nor tasks mention it
- T009 says "Return `ReadResult(file_data=FileData(...))`" with no guidance on construction

**F2: Same-file conflict in parallel group 2 (T016 and T017)**

T016 and T017 are both marked `[P]` but both write to `s3_backend.py`. Concurrent execution will produce a race condition.

### Warnings (WARN — recommend fixing, can proceed)

**W1**: `validate_path()` utility exists in deepagents utils but not planned for use. Spec edge cases mention path traversal prevention.

**W2**: `perform_string_replacement` error-string return branch not mentioned in T011.

**W3**: `fnmatch.fnmatch()` does not support `**` recursive patterns. Upstream uses `wcmatch.glob`. Also `fnmatch.fnmatch("/src/main.py", "*.py")` returns False due to leading `/`.

**W4**: FR-004 vs from_env() inconsistency acknowledged but not formally resolved in tasks.

**W5**: `FileData` and `FileInfo` are TypedDicts, not dataclasses — construction syntax matters.

**W6**: `ls()` behavior for non-existent path vs empty directory unspecified.

**W7**: `write()` "file already exists" returns plain string, not a `FileOperationError` code.

### Observations (informational)

**O1**: Protocol method name upgrade (ls_info→ls etc.) correctly identified and verified.

**O2**: `FileInfo` is TypedDict — dict-literal construction is more idiomatic.

**O3**: moto v5 `@mock_aws` usage is current and correct.

**O4**: boto3 `head_object` returns 403 (not 404) for NoSuchKey with certain IAM policies.

**O5**: contracts/ listed in prerequisites — fine.

**O6**: No task for creating `py.typed` marker file (already exists but not in tasks).

## Recommended Actions

- [ ] **F1-fix**: Update T009 — store raw content in FileData; use `create_file_data()` from utils; do not format with line numbers inside `read()`
- [ ] **F2-fix**: Remove `[P]` from T016 and T017 — they both modify s3_backend.py, must be sequential
- [ ] **W1-fix**: Add `validate_path()` call to T003 scaffold for incoming paths
- [ ] **W2-fix**: Update T011 to mention `str` error-return branch of `perform_string_replacement`
- [ ] **W3-fix**: Clarify T017/T019 — use `fnmatch.fnmatch(path.lstrip("/"), pattern)` or switch to `wcmatch`
- [ ] **W5-fix**: Reference `create_file_data()` and dict-literal syntax for TypedDicts in tasks
- [ ] **W6-fix**: Add design decision note to T008 — empty list for both empty dir and non-existent path
- [ ] **O6-fix**: Add py.typed creation to T005 or T003
