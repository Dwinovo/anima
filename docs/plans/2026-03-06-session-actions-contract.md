# Session Actions Contract Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `Session.actions` as a required create-time rule contract, allow patch-time updates, and enforce event ingestion against the current session action registry.

**Architecture:** Store the current action registry inline on `Session` as JSON, expose it through session create/detail APIs, and validate every event report against the latest session rules before any dual-write happens. Historical events remain untouched; only ingest-time validation changes.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy, Alembic, pytest

---

### Task 1: Lock the request contract with failing tests

**Files:**
- Modify: `tests/presentation/test_session_request_schema.py`
- Modify: `src/presentation/api/schemas/requests/session.py`

**Step 1: Write the failing test**

- Add a create-schema test that requires `actions`.
- Add a patch-schema test that accepts `actions`.
- Add a duplicate-verb rejection test.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/presentation/test_session_request_schema.py -q`

Expected: FAIL because `SessionCreateRequest` and `SessionPatchRequest` do not define `actions`.

### Task 2: Lock usecase behavior with failing tests

**Files:**
- Modify: `tests/usecases/test_session_usecases.py`
- Modify: `tests/usecases/test_event_usecases.py`

**Step 1: Write the failing test**

- Add a create-session usecase test that preserves `actions`.
- Add a patch-session usecase test that updates `actions`.
- Add event-report tests for:
  - unregistered verb
  - target topology mismatch
  - details schema mismatch

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/usecases/test_session_usecases.py tests/usecases/test_event_usecases.py -q`

Expected: FAIL because Session entities/usecases have no `actions`, and event reporting does not validate registry rules.

### Task 3: Implement Session actions request/response/domain plumbing

**Files:**
- Modify: `src/presentation/api/schemas/requests/session.py`
- Modify: `src/presentation/api/schemas/responses/session.py`
- Modify: `src/domain/session/entities.py`
- Modify: `src/domain/session/repository.py`
- Modify: `src/application/usecases/session/create_session.py`
- Modify: `src/application/usecases/session/get_session.py`
- Modify: `src/application/usecases/session/patch_session.py`
- Modify: `src/presentation/api/v1/sessions.py`

**Step 1: Write minimal implementation**

- Define action registry request/response models.
- Thread `actions` through Session domain entity and create/detail/patch flows.
- Keep `GET /sessions` lightweight unless existing tests require otherwise.

**Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/presentation/test_session_request_schema.py tests/usecases/test_session_usecases.py -q`

Expected: PASS.

### Task 4: Persist Session actions in PostgreSQL

**Files:**
- Modify: `src/infrastructure/persistence/postgres/models.py`
- Modify: `src/infrastructure/persistence/postgres/repositories/session_repository.py`
- Create: `alembic/versions/20260306_0005_add_actions_to_sessions.py`

**Step 1: Write minimal implementation**

- Add JSON column for `actions`.
- Map repository create/get/update flows to and from the domain entity.
- Use a migration that safely adds the column for existing rows.

**Step 2: Run focused tests**

Run: `uv run pytest tests/usecases/test_session_usecases.py -q`

Expected: PASS.

### Task 5: Enforce Session actions during event reporting

**Files:**
- Modify: `src/core/exceptions.py`
- Modify: `src/application/usecases/event/report_event.py`
- Modify: `tests/usecases/test_event_usecases.py`
- Modify: `pyproject.toml` if JSON Schema validation support is needed

**Step 1: Write minimal implementation**

- Add a business exception for action-registry validation failures.
- Resolve target topology from `target_ref`.
- Reject unknown verbs, disallowed topologies, and invalid `details`.
- Preserve current dual-write order after validation succeeds.

**Step 2: Run focused tests**

Run: `uv run pytest tests/usecases/test_event_usecases.py -q`

Expected: PASS.

### Task 6: Sync API docs

**Files:**
- Modify: `docs/Anima接口文档.md`
- Modify: `docs/Anima后端规范.md`
- Modify: `docs/Anima客户端设计方案.md`

**Step 1: Update docs**

- Document `Session.actions` request/response shape.
- Document immediate-effect PATCH semantics.
- Document `POST /events` server-side strong validation against current session rules.

**Step 2: Verify consistency**

- Re-read the three docs and ensure the contract matches the code.

### Task 7: Final verification

**Files:**
- Verify only

**Step 1: Run tests**

Run: `uv run pytest tests/presentation/test_session_request_schema.py tests/usecases/test_session_usecases.py tests/usecases/test_event_usecases.py -q`

Expected: PASS.

**Step 2: Run lint**

Run: `uv run ruff check src tests`

Expected: PASS.
