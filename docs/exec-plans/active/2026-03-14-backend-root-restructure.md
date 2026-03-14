# Backend Root Restructure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move the complete Python backend project into `backend/` while keeping `.env` at the repository root and preserving all runtime behavior.

**Architecture:** The package graph stays the same and only the project root changes. We move code, tests, migrations, and Python toolchain files into `backend/`, then update configuration and documentation so `backend/` becomes the authoritative execution root.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Alembic, Redis, MongoDB, Neo4j, uv, pytest, Ruff

---

### Task 1: Register the active plan

**Files:**
- Modify: `H:\anima\docs\exec-plans\active\index.md`
- Create: `H:\anima\docs\exec-plans\active\2026-03-14-backend-root-restructure-design.md`
- Create: `H:\anima\docs\exec-plans\active\2026-03-14-backend-root-restructure.md`

**Step 1: Update the active index**

Add both active documents to the table in `docs/exec-plans/active/index.md` and replace the placeholder row that says there are no active plans.

**Step 2: Verify the index points to the real files**

Run: `Get-ChildItem H:\anima\docs\exec-plans\active`
Expected: both new documents and `index.md` are present.

### Task 2: Move the backend project root

**Files:**
- Create: `H:\anima\backend\`
- Move: `H:\anima\src -> H:\anima\backend\src`
- Move: `H:\anima\tests -> H:\anima\backend\tests`
- Move: `H:\anima\alembic -> H:\anima\backend\alembic`
- Move: `H:\anima\pyproject.toml -> H:\anima\backend\pyproject.toml`
- Move: `H:\anima\uv.lock -> H:\anima\backend\uv.lock`
- Move: `H:\anima\.python-version -> H:\anima\backend\.python-version`
- Move: `H:\anima\alembic.ini -> H:\anima\backend\alembic.ini`
- Move: `H:\anima\.env.example -> H:\anima\backend\.env.example`

**Step 1: Create `backend/`**

Run a filesystem move plan only after confirming the new folder exists.

**Step 2: Move code, tests, migrations, and project files**

Use filesystem move commands, not copy commands, so Git records renames cleanly.

**Step 3: Verify the new tree**

Run: `Get-ChildItem H:\anima\backend`
Expected: all moved project files are visible under `backend/`.

### Task 3: Restore runtime configuration

**Files:**
- Modify: `H:\anima\backend\src\core\config.py`
- Modify: `H:\anima\backend\alembic.ini` if path resolution needs adjustment

**Step 1: Make settings load the root `.env`**

Change the settings model config so the backend can still read `H:\anima\.env` when code is executed from `H:\anima\backend`.

**Step 2: Check Alembic relative paths**

Review `backend/alembic.ini` and confirm `script_location` still resolves now that the file lives under `backend/`.

**Step 3: Verify import/runtime assumptions**

Run: `cd backend && uv run pytest tests/core/test_cors_config.py -q`
Expected: settings initialization still works.

### Task 4: Update root-level maps and references

**Files:**
- Modify: `H:\anima\AGENTS.md`
- Modify: `H:\anima\ARCHITECTURE.md`
- Modify: `H:\anima\docs\index.md`
- Modify: `H:\anima\docs\design-docs\backend-spec.md`
- Modify: `H:\anima\docs\design-docs\api-contract.md`
- Modify: `H:\anima\docs\design-docs\postgres-migrations.md`
- Modify: `H:\anima\docs\generated\db-schema.md`
- Modify: `H:\anima\docs\references\*.txt`
- Modify: any other docs that still point to pre-move root-level backend paths

**Step 1: Rewrite path references**

Replace root-level references like `src/...`, `tests/...`, `alembic/...`, `pyproject.toml` with `backend/src/...`, `backend/tests/...`, `backend/alembic/...`, `backend/pyproject.toml` where the docs are describing filesystem locations.

**Step 2: Rewrite command examples**

Normalize commands to run from `backend/`, or explicitly prefix them with `cd backend &&`.

**Step 3: Re-scan for stale paths**

Run a repository search for old root-level references after edits.

### Task 5: Align ignore rules and workspace expectations

**Files:**
- Modify: `H:\anima\.gitignore`
- Optionally review: `H:\anima\backend\.env.example`

**Step 1: Confirm ignore patterns still match moved caches**

Ensure `.venv/`, `.pytest_cache/`, `.ruff_cache/`, `__pycache__/` still apply when those directories are under `backend/`.

**Step 2: Keep root `.env` behavior explicit**

Do not move `.env`; document in `AGENTS.md` or relevant docs that runtime secrets stay at repo root.

### Task 6: Verify the migrated backend

**Files:**
- Verify only

**Step 1: Run Ruff from the new project root**

Run: `uv run ruff check src tests`
Workdir: `H:\anima\backend`
Expected: `All checks passed!`

**Step 2: Run pytest from the new project root**

Run: `uv run pytest -q`
Workdir: `H:\anima\backend`
Expected: all tests pass.

**Step 3: Check for stale documentation paths**

Run a repo-wide search for legacy root-level backend paths.
Expected: no stale references remain, other than intentional historical text.

**Step 4: Check resulting git diff**

Run: `git status --short`
Expected: root-level backend files show as moved into `backend/`, plus the planned doc updates.
