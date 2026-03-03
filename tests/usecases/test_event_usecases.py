from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from src.application.dto.event import EventReportResult
from src.application.usecases.event.list_session_events import ListSessionEventsUseCase
from src.application.usecases.event.report_event import ReportEventUseCase
from src.core.exceptions import AgentNotFoundException, SessionNotFoundException
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
        name: str | None = None,
        max_agents_limit: int,
        description: str | None = None,
    ) -> Session:
        """创建 Session 并返回实体。"""
        now = datetime.now(timezone.utc)
        created = Session(
            session_id=session_id,
            name=name or session_id,
            description=description,
            max_agents_limit=max_agents_limit,
            created_at=now,
            updated_at=now,
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


class InMemoryProfileRepository:
    """Agent Profile 仓储测试替身。"""

    def __init__(self, existing_agent_ids: set[str] | None = None) -> None:
        """初始化对象并注入所需依赖。"""
        self._existing_agent_ids = existing_agent_ids or set()

    async def save(
        self,
        *,
        session_id: str,
        agent_id: str,
        profile_json: str,
        ttl_seconds: int | None = None,
    ) -> None:
        """占位实现：事件上报测试不会用到此方法。"""
        _ = (session_id, agent_id, profile_json, ttl_seconds)

    async def get(self, *, session_id: str, agent_id: str) -> str | None:
        """读取 Agent 画像，存在时返回占位 JSON。"""
        _ = session_id
        if agent_id in self._existing_agent_ids:
            return '{"name":"demo"}'
        return None

    async def delete(self, *, session_id: str, agent_id: str) -> None:
        """占位实现：事件上报测试不会用到此方法。"""
        _ = (session_id, agent_id)

    async def claim_display_name(
        self,
        *,
        session_id: str,
        agent_id: str,
        display_name: str,
    ) -> bool:
        """占位实现：事件上报测试不会用到此方法。"""
        _ = (session_id, agent_id, display_name)
        return False

    async def release_display_name(
        self,
        *,
        session_id: str,
        agent_id: str,
        display_name: str,
    ) -> None:
        """占位实现：事件上报测试不会用到此方法。"""
        _ = (session_id, agent_id, display_name)


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
            "is_social": is_social,
        }

    async def list_recent_event_ids(
        self,
        *,
        session_id: str,
        limit: int,
        before_world_time: int | None = None,
        before_event_id: str | None = None,
    ) -> list[str]:
        """按时间倒序返回近期事件 ID。"""
        _ = session_id
        _ = limit
        _ = before_world_time
        _ = before_event_id
        return []


class InMemoryGraphSearchRepository:
    """图谱查询仓储测试替身。"""

    def __init__(
        self,
        *,
        calls: list[str],
        recent_ids: list[str] | None = None,
    ) -> None:
        """初始化对象并注入所需依赖。"""
        self._calls = calls
        self._recent_ids = recent_ids or []

    async def upsert_event(
        self,
        *,
        session_id: str,
        event_id: str,
        world_time: int,
        verb: str,
        subject_uuid: str,
        target_ref: str,
        is_social: bool,
    ) -> None:
        """占位实现：列表查询测试不会用到此方法。"""
        _ = (session_id, event_id, world_time, verb, subject_uuid, target_ref, is_social)

    async def list_recent_event_ids(
        self,
        *,
        session_id: str,
        limit: int,
        before_world_time: int | None = None,
        before_event_id: str | None = None,
    ) -> list[str]:
        """返回预置的最近事件结果。"""
        _ = session_id
        _ = before_world_time
        if before_event_id is None:
            recent_ids = list(self._recent_ids)
        else:
            try:
                cursor_index = self._recent_ids.index(before_event_id)
            except ValueError:
                recent_ids = list(self._recent_ids)
            else:
                recent_ids = self._recent_ids[cursor_index + 1 :]
        self._calls.append("neo4j.recent")
        return list(recent_ids[:limit])


@pytest.mark.asyncio
async def test_report_event_usecase_dual_writes_in_order() -> None:
    """验证 Event 上报会先写 Mongo 再写 Neo4j。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        description=None,
        max_agents_limit=100,
    )
    payload_repo = InMemoryEventPayloadRepository()
    profile_repo = InMemoryProfileRepository(existing_agent_ids={"agent_a"})
    graph_repo = InMemoryGraphEventRepository(payload_repo._calls)
    usecase = ReportEventUseCase(session_repo, profile_repo, payload_repo, graph_repo)

    result = await usecase.execute(
        session_id="session_demo",
        world_time=12005,
        subject_uuid="agent_a",
        target_ref="agent_b",
        verb="POSTED",
        details={"content": "hello"},
        schema_version=1,
        is_social=True,
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
    profile_repo = InMemoryProfileRepository(existing_agent_ids={"agent_a"})
    graph_repo = InMemoryGraphEventRepository(payload_repo._calls)
    usecase = ReportEventUseCase(InMemorySessionRepository(), profile_repo, payload_repo, graph_repo)

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
        )


@pytest.mark.asyncio
async def test_report_event_usecase_raises_when_subject_agent_missing() -> None:
    """验证 Subject Agent 不存在时会抛出异常。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        description=None,
        max_agents_limit=100,
    )
    payload_repo = InMemoryEventPayloadRepository()
    profile_repo = InMemoryProfileRepository(existing_agent_ids={"agent_other"})
    graph_repo = InMemoryGraphEventRepository(payload_repo._calls)
    usecase = ReportEventUseCase(session_repo, profile_repo, payload_repo, graph_repo)

    with pytest.raises(AgentNotFoundException):
        await usecase.execute(
            session_id="session_demo",
            world_time=1,
            subject_uuid="agent_a",
            target_ref="agent_b",
            verb="POSTED",
            details={},
            schema_version=1,
            is_social=True,
        )


@pytest.mark.asyncio
async def test_list_session_events_usecase_returns_cursor_page() -> None:
    """验证会话事件列表接口返回首屏分页与 next_cursor。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        description=None,
        max_agents_limit=100,
    )
    payload_repo = InMemoryEventPayloadRepository()
    await payload_repo.put(
        event_id="event_003",
        doc={
            "session_id": "session_demo",
            "world_time": 300,
            "verb": "POSTED",
            "subject_uuid": "agent_a",
            "target_ref": "board:session_demo",
            "details": {"content": "third"},
            "schema_version": 1,
            "is_social": True,
        },
    )
    await payload_repo.put(
        event_id="event_002",
        doc={
            "session_id": "session_demo",
            "world_time": 200,
            "verb": "REPLIED",
            "subject_uuid": "agent_b",
            "target_ref": "event_003",
            "details": {"content": "second"},
            "schema_version": 1,
            "is_social": True,
        },
    )
    await payload_repo.put(
        event_id="event_001",
        doc={
            "session_id": "session_demo",
            "world_time": 100,
            "verb": "LIKED",
            "subject_uuid": "agent_c",
            "target_ref": "event_003",
            "details": {},
            "schema_version": 1,
            "is_social": True,
        },
    )
    graph_repo = InMemoryGraphSearchRepository(
        calls=payload_repo._calls,
        recent_ids=["event_003", "event_002", "event_001"],
    )
    usecase = ListSessionEventsUseCase(session_repo, payload_repo, graph_repo)

    result = await usecase.execute(
        session_id="session_demo",
        limit=2,
        before_world_time=None,
        before_event_id=None,
    )

    assert result.session_id == "session_demo"
    assert [item.event_id for item in result.items] == ["event_003", "event_002"]
    assert result.has_more is True
    assert result.next_cursor == "200:event_002"


@pytest.mark.asyncio
async def test_list_session_events_usecase_uses_cursor_for_next_page() -> None:
    """验证会话事件列表接口可基于 cursor 翻页。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        description=None,
        max_agents_limit=100,
    )
    payload_repo = InMemoryEventPayloadRepository()
    await payload_repo.put(
        event_id="event_003",
        doc={
            "session_id": "session_demo",
            "world_time": 300,
            "verb": "POSTED",
            "subject_uuid": "agent_a",
            "target_ref": "board:session_demo",
            "details": {"content": "third"},
            "schema_version": 1,
            "is_social": True,
        },
    )
    await payload_repo.put(
        event_id="event_002",
        doc={
            "session_id": "session_demo",
            "world_time": 200,
            "verb": "REPLIED",
            "subject_uuid": "agent_b",
            "target_ref": "event_003",
            "details": {"content": "second"},
            "schema_version": 1,
            "is_social": True,
        },
    )
    await payload_repo.put(
        event_id="event_001",
        doc={
            "session_id": "session_demo",
            "world_time": 100,
            "verb": "LIKED",
            "subject_uuid": "agent_c",
            "target_ref": "event_003",
            "details": {},
            "schema_version": 1,
            "is_social": True,
        },
    )
    graph_repo = InMemoryGraphSearchRepository(
        calls=payload_repo._calls,
        recent_ids=["event_003", "event_002", "event_001"],
    )
    usecase = ListSessionEventsUseCase(session_repo, payload_repo, graph_repo)

    result = await usecase.execute(
        session_id="session_demo",
        limit=2,
        before_world_time=200,
        before_event_id="event_002",
    )

    assert [item.event_id for item in result.items] == ["event_001"]
    assert result.has_more is False
    assert result.next_cursor is None


@pytest.mark.asyncio
async def test_list_session_events_usecase_raises_when_session_missing() -> None:
    """验证会话不存在时会抛出异常。"""
    payload_repo = InMemoryEventPayloadRepository()
    graph_repo = InMemoryGraphSearchRepository(calls=payload_repo._calls)
    usecase = ListSessionEventsUseCase(InMemorySessionRepository(), payload_repo, graph_repo)

    with pytest.raises(SessionNotFoundException):
        await usecase.execute(
            session_id="session_missing",
            limit=20,
            before_world_time=None,
            before_event_id=None,
        )
