# Session Target Constraints Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace `allowed_target_topologies` with `target_types`, add `target_constraints` for event/entity targets, and enforce those constraints during event ingestion.

**Architecture:** Keep Session actions inline on `Session`, but promote target validation from a single target-type allowlist to a two-layer model: `target_types` for coarse routing and `target_constraints` for target-specific allowlists. Runtime validation uses existing payload/profile repositories to inspect target metadata only when a matching constraint is declared.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy, Redis profile storage, Mongo payload storage, pytest

---

### Task 1: Lock the new request schema with failing tests

**Files:**
- Modify: `backend/tests/presentation/test_session_request_schema.py`
- Modify: `backend/src/presentation/api/schemas/session_action.py`

**Step 1: Write the failing test**

- Add tests that accept `target_types`.
- Add tests that reject legacy `allowed_target_topologies`.
- Add tests that reject `target_constraints.event` when `target_types` does not include `event`.
- Add tests that reject `target_constraints.entity` when `target_types` does not include `entity`.

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest backend/tests/presentation/test_session_request_schema.py -q`

Expected: FAIL because the current schema still exposes `allowed_target_topologies`.

### Task 2: Lock runtime behavior with failing tests

**Files:**
- Modify: `backend/tests/usecases/test_event_usecases.py`

**Step 1: Write the failing test**

- Add a success case for `target_constraints.event.verb`.
- Add a failure case for target event verb mismatch.
- Add a success case for `target_constraints.entity.source`.
- Add a failure case for target entity source mismatch.
- Add failure cases for missing target metadata when such constraints are declared.

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest backend/tests/usecases/test_event_usecases.py -q`

Expected: FAIL because event reporting currently does not know `target_constraints`.

### Task 3: Replace the action schema and domain shape

**Files:**
- Modify: `backend/src/domain/session/actions.py`
- Modify: `backend/src/presentation/api/schemas/session_action.py`
- Modify: `backend/tests/presentation/test_session_request_schema.py`
- Modify: `backend/tests/usecases/test_session_usecases.py`

**Step 1: Write minimal implementation**

- Rename the field to `target_types`.
- Introduce domain structures for `target_constraints`.
- Keep `verb` and `source` constraints as array allowlists.
- Remove the legacy field from request/response examples and helpers.

**Step 2: Run tests to verify they pass**

Run: `cd backend && uv run pytest backend/tests/presentation/test_session_request_schema.py backend/tests/usecases/test_session_usecases.py -q`

Expected: PASS.

### Task 4: Enforce target constraints during event reporting

**Files:**
- Modify: `backend/src/application/usecases/event/report_event.py`
- Modify: `backend/src/core/exceptions.py` only if new reasons/messages are needed
- Modify: `backend/tests/usecases/test_event_usecases.py`

**Step 1: Write minimal implementation**

- After target type validation, resolve target metadata only for declared constraints.
- For event targets, read target payload and validate `target_constraints.event.verb`.
- For entity targets, read target profile JSON and validate `target_constraints.entity.source`.
- Reject unavailable metadata with a structured `422`.

**Step 2: Run focused tests**

Run: `cd backend && uv run pytest backend/tests/usecases/test_event_usecases.py -q`

Expected: PASS.

### Task 5: Sync docs and examples

**Files:**
- Modify: `docs/Anima接口文档.md`
- Modify: `docs/Anima后端规范.md`
- Modify: `docs/Anima客户端设计方案.md`
- Modify: `docs/Anima管理面板设计文档.md`

**Step 1: Update docs**

- Replace `allowed_target_topologies` with `target_types`.
- Document `target_constraints.event.verb` and `target_constraints.entity.source`.
- Clarify that these fields are allowlist arrays.

**Step 2: Verify consistency**

- Re-read all examples to ensure there is no leftover legacy field name.

### Task 6: Final verification

**Files:**
- Verify only

**Step 1: Run tests**

Run: `cd backend && uv run pytest -q`

Expected: PASS.

**Step 2: Run lint**

Run: `cd backend && uv run ruff check src tests`

Expected: PASS.
