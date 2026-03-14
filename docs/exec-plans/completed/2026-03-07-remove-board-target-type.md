# Board Target Type Removal Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove `board` from the Session action `target_types` enum and treat `board:*` targets as `object`.

**Architecture:** Keep Neo4j physical node labels unchanged as `Entity / Event / Object`. Update the action contract, target type classifier, validation logic, tests, and docs so protocol-level target types match the underlying storage model.

**Tech Stack:** Python, Pydantic, FastAPI, pytest, Markdown docs

---

### Task 1: Update request/schema tests first

**Files:**
- Modify: `H:\anima\tests\presentation\test_session_request_schema.py`
- Modify: `H:\anima\tests\usecases\test_session_usecases.py`
- Modify: `H:\anima\tests\usecases\test_event_usecases.py`

**Step 1: Write the failing test**

- Replace existing `target_types: ["board"]` fixtures with `target_types: ["object"]`.
- Add a request-schema test that rejects `target_types: ["board"]`.

**Step 2: Run test to verify it fails**

Run:

```powershell
cd backend && uv run pytest backend/tests/presentation/test_session_request_schema.py backend/tests/usecases/test_session_usecases.py backend/tests/usecases/test_event_usecases.py -q
```

Expected: FAIL because schema/domain code still accepts `board` and classifies `board:*` as `board`.

### Task 2: Update domain contract and target classification

**Files:**
- Modify: `H:\anima\src\domain\session\actions.py`
- Modify: `H:\anima\src\presentation\api\schemas\session_action.py`

**Step 1: Write minimal implementation**

- Remove `"board"` from the `ActionTargetType` / `SessionActionTargetType` literal.
- Update examples and descriptions from `board` to `object`.
- Change `classify_target_type("board:...")` to return `"object"`.

**Step 2: Run tests**

Run:

```powershell
cd backend && uv run pytest backend/tests/presentation/test_session_request_schema.py backend/tests/usecases/test_session_usecases.py backend/tests/usecases/test_event_usecases.py -q
```

Expected: request/schema tests pass, event tests may still reveal remaining mismatches.

### Task 3: Align event/reporting behavior

**Files:**
- Modify: `H:\anima\src\application\usecases\event\report_event.py`
- Modify: `H:\anima\src\presentation\api\schemas\requests\event.py`

**Step 1: Confirm no board-specific gate remains**

- Ensure event validation only reasons over `entity / event / object`.
- Keep `board:*` examples valid as target refs, but describe them as object references.

**Step 2: Run focused tests**

Run:

```powershell
cd backend && uv run pytest backend/tests/usecases/test_event_usecases.py backend/tests/presentation/test_event_request_schema.py -q
```

Expected: PASS.

### Task 4: Update docs and TS type examples

**Files:**
- Modify: `H:\anima\docs\Anima接口文档.md`
- Modify: `H:\anima\docs\Anima后端规范.md`
- Modify: `H:\anima\docs\Anima客户端设计方案.md`
- Modify: `H:\anima\docs\Anima管理面板设计文档.md`

**Step 1: Replace contract language**

- Replace `board/event/entity/object` with `event/entity/object`.
- Change action examples from `target_types: ["board"]` to `target_types: ["object"]`.
- Explicitly state `board:*` is an object ref convention, not a distinct target type.

### Task 5: Full verification

**Files:**
- No code changes expected

**Step 1: Run full test suite**

```powershell
cd backend && uv run pytest -q
```

Expected: PASS

**Step 2: Run lint**

```powershell
cd backend && uv run ruff check src tests
```

Expected: PASS
