from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from src.application.dto.event import EventReportResult
from src.application.usecases.event.report_event import ReportEventUseCase
from src.application.usecases.event.search_events import SearchEventsUseCase
from src.core.exceptions import SessionNotFoundException
from src.domain.session.entities import Session


class InMemorySessionRepository:
    def __init__(self) -> None:
        """初始化对象并注入所需依赖。"""
        self._sessions: dict[str, Session] = {}

    async def list(self) -> list[Session]:
        """列出全部 Session。"""
        return [self._sessions[key] for key in sorted(self._sessions.keys())]

    async def get(self, *, session_id: str) -> Session | None:
        """按 ID 获取 Session。"""
        return self._sessions.get(session_id)

    async def create(
        self,
        *,
        session_id: str,
        max_agents_limit: int,
        default_llm: str | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> Session:
        """创建 Session 并返回实体。"""
        created = Session(
            session_id=session_id,
            name=name or session_id,
            description=description,
            max_agents_limit=max_agents_limit,
            default_llm=default_llm,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
        )
        self._sessions[session_id] = created
        return created

    async def update_quota(self, *, session_id: str, max_agents_limit: int) -> None:
        """更新 Session 配额。"""
        existing = self._sessions.get(session_id)
        if existing is None:
            return
        existing.max_agents_limit = max_agents_limit

    async def delete(self, *, session_id: str) -> None:
        """删除 Session。"""
        self._sessions.pop(session_id, None)


class InMemoryEventPayloadRepository:
    def __init__(self) -> None:
        """初始化对象并注入所需依赖。"""
        self._docs: dict[str, dict[str, Any]] = {}
        self._calls: list[str] = []

    async def put(self, *, event_id: str, doc: dict[str, Any]) -> None:
        """写入 Event payload。"""
        self._calls.append("mongo.put")
        self._docs[event_id] = dict(doc)

    async def get(self, *, event_id: str) -> dict[str, Any] | None:
        """读取单条 Event payload。"""
        return self._docs.get(event_id)

    async def mget(self, *, event_ids: list[str]) -> dict[str, dict[str, Any]]:
        """批量读取 Event payload。"""
        self._calls.append("mongo.mget")
        return {event_id: self._docs[event_id] for event_id in event_ids if event_id in self._docs}


class InMemoryGraphEventRepository:
    def __init__(self, calls: list[str]) -> None:
        """初始化对象并注入所需依赖。"""
        self._events: dict[str, dict[str, Any]] = {}
        self._calls = calls

    async def upsert_event(
        self,
        *,
        session_id: str,
        event_id: str,
        world_time: int,
        verb: str,
        subject_uuid: str,
        target_ref: str,
        embedding_256: list[float] | None,
        is_social: bool,
    ) -> None:
        """写入或更新 Event 骨架。"""
        self._calls.append("neo4j.upsert")
        self._events[event_id] = {
            "session_id": session_id,
            "world_time": world_time,
            "verb": verb,
            "subject_uuid": subject_uuid,
            "target_ref": target_ref,
            "embedding_256": embedding_256,
            "is_social": is_social,
        }

    async def topology_filter_event_ids(
        self,
        *,
        session_id: str,
        event_ids: list[str],
        anchor_uuid: str,
        limit: int,
    ) -> list[str]:
        """执行拓扑过滤并返回事件 ID。"""
        _ = session_id
        _ = event_ids
        _ = anchor_uuid
        _ = limit
        return []

    async def list_recent_event_ids(
        self,
        *,
        session_id: str,
        limit: int,
    ) -> list[str]:
        """按时间倒序返回近期事件 ID。"""
        _ = session_id
        _ = limit
        return []


class InMemoryGraphSearchRepository:
    def __init__(
        self,
        *,
        calls: list[str],
        recent_ids: list[str] | None = None,
        topology_ids: list[str] | None = None,
    ) -> None:
        """初始化对象并注入所需依赖。"""
        self._calls = calls
        self._recent_ids = recent_ids or []
        self._topology_ids = topology_ids or []

    async def upsert_event(
        self,
        *,
        session_id: str,
        event_id: str,
        world_time: int,
        verb: str,
        subject_uuid: str,
        target_ref: str,
        embedding_256: list[float] | None,
        is_social: bool,
    ) -> None:
        """占位实现：检索测试不会用到此方法。"""
        _ = (
            session_id,
            event_id,
            world_time,
            verb,
            subject_uuid,
            target_ref,
            embedding_256,
            is_social,
        )

    async def list_recent_event_ids(
        self,
        *,
        session_id: str,
        limit: int,
    ) -> list[str]:
        """返回预置的最近事件结果。"""
        _ = session_id
        _ = limit
        self._calls.append("neo4j.recent")
        return list(self._recent_ids)

    async def topology_filter_event_ids(
        self,
        *,
        session_id: str,
        event_ids: list[str],
        anchor_uuid: str,
        limit: int,
    ) -> list[str]:
        """返回预置的拓扑过滤结果。"""
        _ = session_id
        _ = event_ids
        _ = anchor_uuid
        _ = limit
        self._calls.append("neo4j.topology")
        return list(self._topology_ids)


@pytest.mark.asyncio
async def test_report_event_usecase_dual_writes_in_order() -> None:
    """验证 Event 上报会先写 Mongo 再写 Neo4j。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        name="Demo",
        description=None,
        max_agents_limit=100,
        default_llm="gpt-4o",
    )
    payload_repo = InMemoryEventPayloadRepository()
    graph_repo = InMemoryGraphEventRepository(payload_repo._calls)
    usecase = ReportEventUseCase(session_repo, payload_repo, graph_repo)

    result = await usecase.execute(
        session_id="session_demo",
        world_time=12005,
        subject_uuid="agent_a",
        target_ref="agent_b",
        verb="POSTED",
        details={"content": "hello"},
        schema_version=1,
        is_social=True,
        embedding_256=None,
    )

    assert isinstance(result, EventReportResult)
    assert result.session_id == "session_demo"
    assert result.event_id.startswith("event_")
    assert result.world_time == 12005
    assert result.verb == "POSTED"
    assert result.accepted is True
    assert payload_repo._calls == ["mongo.put", "neo4j.upsert"]
    payload_doc = await payload_repo.get(event_id=result.event_id)
    assert payload_doc is not None
    assert payload_doc["session_id"] == "session_demo"
    assert payload_doc["world_time"] == 12005
    assert payload_doc["verb"] == "POSTED"
    assert payload_doc["subject_uuid"] == "agent_a"
    assert payload_doc["target_ref"] == "agent_b"
    assert payload_doc["details"] == {"content": "hello"}
    assert payload_doc["schema_version"] == 1
    assert payload_doc["is_social"] is True
    assert graph_repo._events[result.event_id]["verb"] == "POSTED"


@pytest.mark.asyncio
async def test_report_event_usecase_raises_when_session_missing() -> None:
    """验证 Session 不存在时会抛出异常。"""
    payload_repo = InMemoryEventPayloadRepository()
    graph_repo = InMemoryGraphEventRepository(payload_repo._calls)
    usecase = ReportEventUseCase(InMemorySessionRepository(), payload_repo, graph_repo)

    with pytest.raises(SessionNotFoundException):
        await usecase.execute(
            session_id="session_missing",
            world_time=1,
            subject_uuid="agent_a",
            target_ref="agent_b",
            verb="POSTED",
            details={},
            schema_version=1,
            is_social=True,
            embedding_256=None,
        )


@pytest.mark.asyncio
async def test_search_events_usecase_uses_recent_then_topology_then_hydration() -> None:
    """验证检索流程会按“近期候选->拓扑->水合”顺序执行。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        name="Demo",
        description=None,
        max_agents_limit=100,
        default_llm="gpt-4o",
    )
    payload_repo = InMemoryEventPayloadRepository()
    await payload_repo.put(
        event_id="event_a",
        doc={
            "session_id": "session_demo",
            "world_time": 100,
            "verb": "POSTED",
            "subject_uuid": "agent_x",
            "target_ref": "agent_y",
            "details": {"content": "A"},
            "schema_version": 1,
            "is_social": True,
        },
    )
    await payload_repo.put(
        event_id="event_b",
        doc={
            "session_id": "session_demo",
            "world_time": 120,
            "verb": "REPLIED",
            "subject_uuid": "agent_z",
            "target_ref": "event_a",
            "details": {"content": "B"},
            "schema_version": 1,
            "is_social": True,
        },
    )
    graph_repo = InMemoryGraphSearchRepository(
        calls=payload_repo._calls,
        recent_ids=["event_a", "event_b", "event_c"],
        topology_ids=["event_b", "event_a"],
    )
    usecase = SearchEventsUseCase(session_repo, payload_repo, graph_repo)

    result = await usecase.execute(
        session_id="session_demo",
        anchor_uuid="agent_me",
        limit=2,
        candidate_limit=8,
    )

    assert result.session_id == "session_demo"
    assert result.total == 2
    assert [item.event_id for item in result.items] == ["event_b", "event_a"]
    assert result.items[0].verb == "REPLIED"
    assert result.items[1].details == {"content": "A"}
    assert payload_repo._calls == [
        "mongo.put",
        "mongo.put",
        "neo4j.recent",
        "neo4j.topology",
        "mongo.mget",
    ]


@pytest.mark.asyncio
async def test_search_events_usecase_uses_recent_candidates() -> None:
    """验证检索流程会走“近期候选->拓扑->水合”路径。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        name="Demo",
        description=None,
        max_agents_limit=100,
        default_llm="gpt-4o",
    )
    payload_repo = InMemoryEventPayloadRepository()
    await payload_repo.put(
        event_id="event_r1",
        doc={
            "session_id": "session_demo",
            "world_time": 101,
            "verb": "POSTED",
            "subject_uuid": "agent_x",
            "target_ref": "agent_y",
            "details": {"content": "R1"},
            "schema_version": 1,
            "is_social": True,
        },
    )
    graph_repo = InMemoryGraphSearchRepository(
        calls=payload_repo._calls,
        recent_ids=["event_r1"],
        topology_ids=["event_r1"],
    )
    usecase = SearchEventsUseCase(session_repo, payload_repo, graph_repo)

    result = await usecase.execute(
        session_id="session_demo",
        anchor_uuid="agent_me",
        limit=5,
        candidate_limit=20,
    )

    assert result.total == 1
    assert result.items[0].event_id == "event_r1"
    assert payload_repo._calls == [
        "mongo.put",
        "neo4j.recent",
        "neo4j.topology",
        "mongo.mget",
    ]


@pytest.mark.asyncio
async def test_search_events_usecase_raises_when_session_missing() -> None:
    """验证 Session 不存在时检索会抛出异常。"""
    payload_repo = InMemoryEventPayloadRepository()
    graph_repo = InMemoryGraphSearchRepository(calls=payload_repo._calls)
    usecase = SearchEventsUseCase(InMemorySessionRepository(), payload_repo, graph_repo)

    with pytest.raises(SessionNotFoundException):
        await usecase.execute(
            session_id="session_missing",
            anchor_uuid="agent_me",
            limit=5,
            candidate_limit=20,
        )
