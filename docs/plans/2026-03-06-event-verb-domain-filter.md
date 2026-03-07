# Event Verb Domain Filter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add optional verb-domain filtering to the session event listing API while preserving current pagination semantics.

**Architecture:** Extend the request schema and use case to carry an optional `verb_domain` value, then apply the filter in the Neo4j recent-event lookup by matching `verb` prefixes. Keep response payloads unchanged so existing clients remain compatible.

**Tech Stack:** FastAPI, Pydantic, Neo4j, pytest

---

### Task 1: Add failing tests for the new query contract

**Files:**
- Modify: `tests/presentation/test_event_list_query_schema.py`
- Modify: `tests/usecases/test_event_usecases.py`
- Modify: `tests/infrastructure/test_neo4j_graph_event_repository.py`

**Step 1: Write the failing tests**

- Add a schema test that accepts `verb_domain=social`.
- Add a schema test that rejects invalid values such as `social.posted`.
- Add a use case test that verifies `verb_domain` is forwarded to the graph repository.
- Add an infrastructure test that verifies the Neo4j recent-event query includes a verb-prefix clause.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/presentation/test_event_list_query_schema.py tests/usecases/test_event_usecases.py tests/infrastructure/test_neo4j_graph_event_repository.py -q`

Expected: FAIL because `verb_domain` is not part of the request schema or repository contract yet.

### Task 2: Implement the minimal code path

**Files:**
- Modify: `src/presentation/api/schemas/requests/event.py`
- Modify: `src/presentation/api/v1/events.py`
- Modify: `src/application/usecases/event/list_session_events.py`
- Modify: `src/domain/memory/graph_event_repository.py`
- Modify: `src/infrastructure/persistence/neo4j/graph_event_repository.py`
- Modify: `src/infrastructure/persistence/neo4j/cypher.py`
- Modify: `tests/usecases/test_event_usecases.py`

**Step 1: Write minimal implementation**

- Add `verb_domain` to `EventListQuery` with namespace-only validation.
- Pass `verb_domain` from the router to the use case and repository.
- Build a `verb_prefix` in the Neo4j repository and apply it in `RECENT_EVENT_IDS`.

**Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/presentation/test_event_list_query_schema.py tests/usecases/test_event_usecases.py tests/infrastructure/test_neo4j_graph_event_repository.py -q`

Expected: PASS.

### Task 3: Update product and API documentation

**Files:**
- Modify: `docs/Anima接口文档.md`
- Modify: `docs/Anima后端规范.md`
- Modify: `docs/Anima客户端设计方案.md`

**Step 1: Update docs**

- Document the new `verb_domain` query parameter.
- Clarify validation and filtered pagination semantics.
- Add an example request using `verb_domain=social`.

**Step 2: Verify documentation consistency**

- Re-read each updated section and ensure naming and examples match the implemented contract.

### Task 4: Full verification

**Files:**
- Verify only

**Step 1: Run focused verification**

Run: `uv run pytest tests/presentation/test_event_list_query_schema.py tests/usecases/test_event_usecases.py tests/infrastructure/test_neo4j_graph_event_repository.py -q`

Expected: PASS.

**Step 2: Run broader regression checks**

Run: `uv run pytest tests/presentation/test_events_api_exposure.py tests/presentation/test_event_list_query_schema.py tests/usecases/test_event_usecases.py tests/infrastructure/test_neo4j_graph_event_repository.py tests/infrastructure/test_neo4j_schema.py -q`

Expected: PASS.
