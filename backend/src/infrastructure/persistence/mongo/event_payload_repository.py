from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from src.domain.memory.event_payload_repository import EventPayloadRepository
from src.infrastructure.persistence.mongo.collections import EVENT_PAYLOADS_COLLECTION


class MongoEventPayloadRepository(EventPayloadRepository):
    """Mongo 侧 Event details（payload/血肉载荷）仓储实现。"""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        """初始化对象并注入所需依赖。"""
        self._col = db[EVENT_PAYLOADS_COLLECTION]

    async def put(self, *, event_id: str, doc: dict[str, Any]) -> None:
        """
        幂等写入：使用 upsert。
        推荐 doc 至少包含：
          - session_id: str
          - world_time: int
          - verb: str
          - details: dict[str, Any]
          - schema_version: int
        """
        # 强制 _id = event_id，保证寻址一致、天然唯一
        stored = dict(doc)
        stored["_id"] = event_id

        # 统一补齐 created_at（如果未提供）
        stored.setdefault("created_at", datetime.now(timezone.utc).isoformat())

        await self._col.update_one(
            {"_id": event_id},
            {"$set": stored},
            upsert=True,
        )

    async def get(self, *, event_id: str) -> dict[str, Any] | None:
        """执行 `get` 相关逻辑。"""
        doc = await self._col.find_one({"_id": event_id})
        return doc

    async def mget(self, *, event_ids: list[str]) -> dict[str, dict[str, Any]]:
        """批量读取并返回数据。"""
        if not event_ids:
            return {}

        cursor = self._col.find({"_id": {"$in": event_ids}})
        docs = await cursor.to_list(length=len(event_ids))

        # 返回映射：event_id -> doc，方便 hydration 对齐
        out: dict[str, dict[str, Any]] = {}
        for d in docs:
            _id = d.get("_id")
            if isinstance(_id, str):
                out[_id] = d
        return out