# Session Actions Verb-And-Schema-Only Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reduce `Session.actions` to `verb + description + details_schema` and remove all server-side target routing constraints.

**Architecture:** Keep `target_ref` as an opaque reference that the server stores and returns without semantic routing validation. Session actions remain a registry of allowed verbs plus payload schemas; event ingestion only validates session existence, subject existence, registered verb, and `details_schema`.

**Tech Stack:** Python, Pydantic, FastAPI, pytest, Markdown docs

---

### Task 1: Rewrite request and usecase tests first

**Files:**
- Modify: `H:\anima\tests\presentation\test_session_request_schema.py`
- Modify: `H:\anima\tests\usecases\test_session_usecases.py`
- Modify: `H:\anima\tests\usecases\test_event_usecases.py`

**Step 1: Write the failing tests**

- Remove `target_types` from action fixtures.
- Remove `target_constraints` test fixtures.
- Replace target-routing rejection tests with acceptance tests showing any `target_ref` is allowed once `verb` and `details_schema` pass.
- Add request-schema tests that reject `target_types` and `target_constraints` as unexpected fields.

**Step 2: Run test to verify it fails**

Run:

```powershell
uv run pytest tests/presentation/test_session_request_schema.py tests/usecases/test_session_usecases.py tests/usecases/test_event_usecases.py -q
```

Expected: FAIL because production schema/domain/usecase still requires or reads target control fields.

### Task 2: Shrink the Session action contract

**Files:**
- Modify: `H:\anima\src\domain\session\actions.py`
- Modify: `H:\anima\src\presentation\api\schemas\session_action.py`

**Step 1: Write minimal implementation**

- Remove `target_types` and `target_constraints` from `SessionAction`.
- Remove related helper types and parsers.
- Keep serialization compatible by ignoring legacy keys when loading persisted actions.
- Update Pydantic schema to only expose `verb`, `description`, `details_schema`.

**Step 2: Run focused tests**

Run:

```powershell
uv run pytest tests/presentation/test_session_request_schema.py tests/usecases/test_session_usecases.py -q
```

Expected: PASS.

### Task 3: Remove target-routing validation from event ingestion

**Files:**
- Modify: `H:\anima\src\application\usecases\event\report_event.py`

**Step 1: Write minimal implementation**

- Delete target type checks.
- Delete target constraint checks.
- Keep `verb` registration and `details_schema` validation.

**Step 2: Run focused tests**

Run:

```powershell
uv run pytest tests/usecases/test_event_usecases.py -q
```

Expected: PASS.

### Task 4: Update docs and examples

**Files:**
- Modify: `H:\anima\docs\Anima接口文档.md`
- Modify: `H:\anima\docs\Anima后端规范.md`
- Modify: `H:\anima\docs\Anima客户端设计方案.md`
- Modify: `H:\anima\docs\Anima管理面板设计文档.md`

**Step 1: Replace contract descriptions**

- Change action examples to only show `verb`, `description`, `details_schema`.
- State that `target_ref` is opaque to the service layer.
- Remove all `target_types` / `target_constraints` guidance from main docs.

### Task 5: Full verification

**Step 1: Run full test suite**

```powershell
uv run pytest -q
```

Expected: PASS

**Step 2: Run lint**

```powershell
uv run ruff check src tests
```

Expected: PASS
