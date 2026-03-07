# Context v2 Domain-Neutral Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the current social-specific `Context` contract with a domain-neutral `Context v2` contract that returns generic relation views.

**Architecture:** Keep the service responsible for graph-backed event aggregation and pagination, but rename and recalculate `Context` views so they reflect generic relationship semantics rather than social-product semantics. Clients continue to interpret these views locally into domain-specific feeds, prompts, and tools.

**Tech Stack:** FastAPI, Pydantic, Neo4j, MongoDB, pytest

---

### Task 1: Lock the target contract with failing tests

**Files:**
- Modify: `tests/usecases/test_get_entity_context_usecase.py`
- Modify: `src/presentation/api/schemas/responses/entity.py`
- Modify: `tests/presentation/` (add or extend response-shape tests if needed)

**Step 1: Write the failing test**

- Add tests that expect `views` to expose `self_recent`, `incoming_recent`, `neighbor_recent`, `global_recent`, `hot_targets`, and `world_snapshot`.
- Add tests that reject or stop asserting legacy fields such as `public_feed`, `following_feed`, `attention`, and `my_following_count`.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/usecases/test_get_entity_context_usecase.py -q`

Expected: FAIL because the current use case still emits legacy social views.

### Task 2: Update DTOs and response schema

**Files:**
- Modify: `src/application/dto/entity.py`
- Modify: `src/presentation/api/schemas/responses/entity.py`
- Test: `tests/usecases/test_get_entity_context_usecase.py`

**Step 1: Write minimal implementation**

- Rename view fields in DTOs and API schemas to the new `Context v2` names.
- Remove `my_following_count` from the guaranteed `world_snapshot` contract.

**Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/usecases/test_get_entity_context_usecase.py -q`

Expected: PASS for schema and DTO contract updates, with use case logic still to be updated next.

### Task 3: Rebuild context assembly logic around generic graph semantics

**Files:**
- Modify: `src/application/usecases/entity/get_entity_context.py`
- Modify: `src/domain/memory/graph_event_repository.py` only if query needs expand
- Test: `tests/usecases/test_get_entity_context_usecase.py`

**Step 1: Write minimal implementation**

- Compute `incoming_recent` using direct target-to-entity and target-to-self-event rules.
- Compute `neighbor_recent` from recent direct entity-to-entity interaction neighborhood, not from `social.followed`.
- Compute `global_recent` as the recent session-wide event slice.
- Keep `hot_targets` aggregation generic over `target_ref`.

**Step 2: Run tests to verify it passes**

Run: `uv run pytest tests/usecases/test_get_entity_context_usecase.py -q`

Expected: PASS.

### Task 4: Update API docs and client docs after code lands

**Files:**
- Modify: `docs/Anima接口文档.md`
- Modify: `docs/Anima后端规范.md`
- Modify: `docs/Anima客户端设计方案.md`

**Step 1: Sync docs**

- Remove legacy social-view wording from the implemented contract.
- Keep client-side social examples explicitly framed as projections built on top of generic context views.

**Step 2: Verify consistency**

- Re-read all three docs and confirm view names, field names, and semantics match the code.

### Task 5: Final verification

**Files:**
- Verify only

**Step 1: Run focused tests**

Run: `uv run pytest tests/usecases/test_get_entity_context_usecase.py tests/presentation -q`

Expected: PASS.

**Step 2: Run lint**

Run: `uv run ruff check src/application/usecases/entity/get_entity_context.py src/application/dto/entity.py src/presentation/api/schemas/responses/entity.py tests/usecases/test_get_entity_context_usecase.py`

Expected: PASS.
