# Monorepo Frontend Docs Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Align repository docs and ignore rules with the new `apps/admin` frontend managed alongside `backend/`.

**Architecture:** Update repo entry docs to treat `apps/admin/` and `backend/` as one monorepo, revise stale status/spec files that still describe the frontend as external, and centralize Next.js ignore rules in the root `.gitignore`. No runtime behavior changes are included.

**Tech Stack:** Markdown, `.gitignore`, Next.js 16, React 19, FastAPI documentation.

---

### Task 1: Register the change in active exec plans

**Files:**
- Create: `docs/exec-plans/active/2026-03-14-monorepo-frontend-docs-design.md`
- Create: `docs/exec-plans/active/2026-03-14-monorepo-frontend-docs.md`
- Modify: `docs/exec-plans/active/index.md`

**Step 1: Write the design note**

Document why the repo map and ignore rules need to change now that `apps/admin/` exists.

**Step 2: Write the implementation plan**

Record the exact files to update and the verification approach for doc consistency.

**Step 3: Register both files in `active/index.md`**

Make sure the active plans index stays navigable for the next Agent.

**Step 4: Verify the index entry exists**

Run: `Get-Content -Raw docs/exec-plans/active/index.md`

Expected: the new design and plan files both appear in the table.

### Task 2: Update repo map and frontend-facing documents

**Files:**
- Modify: `AGENTS.md`
- Modify: `ARCHITECTURE.md`
- Modify: `docs/index.md`
- Modify: `docs/FRONTEND.md`
- Modify: `docs/product-specs/admin-console-spec.md`
- Modify: `docs/product-specs/index.md`

**Step 1: Update the repository identity**

Rewrite entry docs so they describe the repo as a monorepo with `backend/` and `apps/admin/`.

**Step 2: Update frontend status**

Replace stale “frontend not in repo” wording with the actual state: `apps/admin/` exists, but it is still scaffold-level.

**Step 3: Link specs to implementation**

Point the management console spec at `apps/admin/` so product intent and code location stay connected.

**Step 4: Verify stale wording is gone**

Run: `Get-ChildItem -Recurse -File docs | Select-String -Pattern '当前仓库没有前端源码|目前本仓库没有对应前端实现源码|实现仓|跨仓|未入仓|前端源码'`

Expected: no matches in current entry, plan, or product-status docs.

### Task 3: Update status docs and centralize ignore rules

**Files:**
- Modify: `.gitignore`
- Delete: `apps/admin/.gitignore`
- Modify: `docs/PLANS.md`
- Modify: `docs/QUALITY_SCORE.md`
- Modify: `docs/PRODUCT_SENSE.md`
- Modify: `docs/exec-plans/tech-debt-tracker.md`

**Step 1: Move Next.js ignore rules to the repo root**

Merge the admin app ignore rules into `.gitignore` so the monorepo has a single ignore entrypoint.

**Step 2: Remove the app-local ignore file**

Delete `apps/admin/.gitignore` after the root rules cover the same artifacts.

**Step 3: Update project state docs**

Reflect that the admin app is now in-repo, but still missing business pages, data access, and test coverage.

**Step 4: Run final verification**

Run: `git diff --check`

Expected: no whitespace or merge-marker issues in the edited files.
