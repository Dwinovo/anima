from __future__ import annotations

from typing import Any, Protocol


class EventPayloadRepository(Protocol):
    async def put(self, *, event_id: str, doc: dict[str, Any]) -> None:
        """写入单条事件载荷。"""
        ...

    async def get(self, *, event_id: str) -> dict[str, Any] | None:
        """读取单条事件载荷。"""
        ...

    async def mget(self, *, event_ids: list[str]) -> dict[str, dict[str, Any]]:
        """批量读取事件载荷并按 event_id 返回。"""
        ...
