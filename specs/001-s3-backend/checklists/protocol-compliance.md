# Protocol Compliance Checklist: S3 Backend for deepagents

**Purpose**: Validate that requirements are complete, clear, and consistent for implementing BackendProtocol against S3
**Created**: 2026-03-20
**Feature**: [spec.md](../spec.md)

## Requirement Completeness

- [ ] CHK001 - Are all eight BackendProtocol method signatures explicitly mapped to S3 API calls? [Completeness, Spec §FR-001]
- [ ] CHK002 - Are return types specified for each method matching the protocol's dataclass definitions (ReadResult, WriteResult, etc.)? [Completeness, Spec §FR-002]
- [ ] CHK003 - Is the `ReadResult.file_data` construction specified, including how `created_at` and `modified_at` are populated from S3 metadata? [Gap]
- [ ] CHK004 - Are `files_update` semantics documented for WriteResult and EditResult (should be None for external storage)? [Completeness, Plan §Architecture]
- [ ] CHK005 - Is the behavior for `read()` when `offset` exceeds the number of lines specified? [Gap, Edge Case]
- [ ] CHK006 - Are pagination requirements for `ls()` documented (S3 list_objects_v2 returns max 1000 per page)? [Completeness, Spec §FR-001]

## Requirement Clarity

- [ ] CHK007 - Is the exact prefix normalization rule unambiguous (e.g., `"agent"` → `"agent/"`, `"agent/"` → `"agent/"`, `""` → `""`)? [Clarity, Spec §FR-007]
- [ ] CHK008 - Is "literal text search" in grep clearly distinguished from regex (does it handle special regex characters as literals)? [Clarity, Spec §FR-011]
- [ ] CHK009 - Is the 10MB file size threshold for grep defined precisely (10 * 1024 * 1024 bytes vs 10,000,000 bytes)? [Clarity, Spec §FR-011]
- [ ] CHK010 - Is the `write()` "file already exists" check method specified (head_object vs get_object)? [Clarity, Plan §Method Map]
- [ ] CHK011 - Is the `from_env()` error behavior for missing `S3_BACKEND_BUCKET` specified as raising ValueError vs returning error? [Clarity, Spec §FR-006]

## Requirement Consistency

- [ ] CHK012 - Are error handling requirements consistent between spec ("never raise exceptions") and `from_env()` acceptance scenario ("clear error is raised")? [Conflict, Spec §FR-004 vs §US4-AS2]
- [ ] CHK013 - Are the glob pattern matching semantics consistent between `grep(glob=...)` filter and `glob()` method? [Consistency, Spec §FR-011 vs §FR-012]
- [ ] CHK014 - Is the path normalization behavior consistent across all eight methods (leading `/`, trailing `/` handling)? [Consistency, Spec §FR-007]

## Acceptance Criteria Quality

- [ ] CHK015 - Are acceptance scenarios for `edit()` covering both `replace_all=True` and `replace_all=False` cases? [Coverage, Spec §US1]
- [ ] CHK016 - Can the success criterion "installs cleanly via pip install" be objectively measured? [Measurability, Spec §SC-002]
- [ ] CHK017 - Are the specific ruff rules the code must pass documented or referenced? [Measurability, Spec §SC-005]

## Scenario Coverage

- [ ] CHK018 - Are requirements defined for `grep()` when the search path doesn't exist in S3? [Gap, Exception Flow]
- [ ] CHK019 - Are requirements defined for `glob()` with no matching files? [Gap, Edge Case]
- [ ] CHK020 - Are requirements defined for `ls()` on an empty directory (no objects under prefix)? [Gap, Edge Case]
- [ ] CHK021 - Are requirements defined for `download_files()` with an empty paths list? [Gap, Edge Case]
- [ ] CHK022 - Are concurrent access requirements specified (two agents editing the same file)? [Gap, Non-Functional]

## Edge Case Coverage

- [ ] CHK023 - Is behavior specified when S3 key contains special characters (spaces, unicode)? [Edge Case, Gap]
- [ ] CHK024 - Is behavior specified when `edit()` receives `old_string == new_string`? [Edge Case, Gap]
- [ ] CHK025 - Is behavior specified when `write()` content is empty string? [Edge Case, Gap]
- [ ] CHK026 - Are requirements defined for handling S3 eventual consistency (read-after-write for new objects)? [Edge Case, Gap]
- [ ] CHK027 - Is behavior specified when virtual path is exactly `/` for `read()` and `write()`? [Edge Case, Gap]

## Dependencies & Assumptions

- [ ] CHK028 - Is the minimum boto3 version requirement justified against needed S3 API features? [Assumption, Plan §Dependencies]
- [ ] CHK029 - Is the deepagents version compatibility documented (which protocol version is targeted)? [Dependency, Gap]
- [ ] CHK030 - Is the assumption that S3 `LastModified` serves as both `created_at` and `modified_at` documented? [Assumption, Research §R4]
