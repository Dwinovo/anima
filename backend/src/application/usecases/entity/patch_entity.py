from __future__ import annotations

import json
from hashlib import sha1

from src.application.dto.entity import EntityLifecycleResult
from src.core.exceptions import (
    DisplayNameAllocationException,
    EntityNotFoundException,
    SessionNotFoundException,
)
from src.domain.entity.presence_repository import EntityPresenceRepository
from src.domain.entity.profile_repository import EntityProfileRepository
from src.domain.session.repository import SessionRepository

DISPLAY_NAME_SPACE_SIZE = 100000


class PatchEntityUseCase:
    """更新 Entity 昵称并重算唯一展示名。"""

    def __init__(
        self,
        session_repo: SessionRepository,
        presence_repo: EntityPresenceRepository,
        profile_repo: EntityProfileRepository,
    ) -> None:
        """初始化对象并注入所需依赖。"""
        self._session_repo = session_repo
        self._presence_repo = presence_repo
        self._profile_repo = profile_repo

    @staticmethod
    def _suffix_seed(*, session_id: str, entity_id: str) -> int:
        """基于 session_id+entity_id 生成稳定的数字后缀起点。"""
        digest = sha1(f"{session_id}:{entity_id}".encode("utf-8"), usedforsecurity=False).hexdigest()
        return int(digest[:8], 16) % DISPLAY_NAME_SPACE_SIZE

    @staticmethod
    def _build_display_name(*, name: str, suffix_number: int) -> str:
        """根据昵称与后缀拼接展示名。"""
        return f"{name}#{suffix_number:05d}"

    async def execute(
        self,
        *,
        session_id: str,
        entity_id: str,
        name: str | None = None,
    ) -> EntityLifecycleResult:
        """执行业务流程并返回结果。"""
        session = await self._session_repo.get(session_id=session_id)
        if session is None:
            raise SessionNotFoundException(session_id)

        profile_json = await self._profile_repo.get(session_id=session_id, entity_id=entity_id)
        is_active = await self._presence_repo.is_active(session_id=session_id, entity_id=entity_id)
        if profile_json is None and not is_active:
            raise EntityNotFoundException(session_id=session_id, uuid=entity_id)

        current = self._parse_profile_payload(profile_json)
        next_name = current.get("name")
        next_display_name = current.get("display_name")
        next_source = current.get("source")

        if name is not None:
            base_suffix = self._suffix_seed(session_id=session_id, entity_id=entity_id)
            allocated_display_name = await self._allocate_unique_display_name(
                session_id=session_id,
                entity_id=entity_id,
                name=name,
                base_suffix=base_suffix,
            )
            previous_display_name = current.get("display_name")
            if previous_display_name and previous_display_name != allocated_display_name:
                await self._profile_repo.release_display_name(
                    session_id=session_id,
                    entity_id=entity_id,
                    display_name=previous_display_name,
                )
            next_name = name
            next_display_name = allocated_display_name

        updated_profile_payload = {
            "name": next_name,
            "display_name": next_display_name,
            "source": next_source,
        }
        updated_profile_json = json.dumps(updated_profile_payload, ensure_ascii=False, separators=(",", ":"))
        await self._profile_repo.save(
            session_id=session_id,
            entity_id=entity_id,
            profile_json=updated_profile_json,
        )

        return EntityLifecycleResult(
            session_id=session_id,
            entity_id=entity_id,
            active=is_active,
            name=next_name,
            display_name=next_display_name,
            source=next_source,
        )

    async def _allocate_unique_display_name(
        self,
        *,
        session_id: str,
        entity_id: str,
        name: str,
        base_suffix: int,
    ) -> str:
        """分配同 Session 内唯一展示名，不可用时线性探测后缀空间。"""
        for offset in range(DISPLAY_NAME_SPACE_SIZE):
            suffix = (base_suffix + offset) % DISPLAY_NAME_SPACE_SIZE
            candidate = self._build_display_name(name=name, suffix_number=suffix)
            claimed = await self._profile_repo.claim_display_name(
                session_id=session_id,
                entity_id=entity_id,
                display_name=candidate,
            )
            if claimed:
                return candidate
        raise DisplayNameAllocationException(session_id=session_id, name=name)

    @staticmethod
    def _parse_profile_payload(profile_json: str | None) -> dict[str, str | None]:
        """解析 Redis 画像缓存为结构化字段。"""
        if profile_json is None:
            return {"name": None, "display_name": None, "source": None}

        try:
            payload = json.loads(profile_json)
        except json.JSONDecodeError:
            return {"name": None, "display_name": None, "source": None}

        if not isinstance(payload, dict):
            return {"name": None, "display_name": None, "source": None}

        display_name = payload.get("display_name")
        source = payload.get("source")
        return {
            "name": payload.get("name") if isinstance(payload.get("name"), str) else None,
            "display_name": display_name if isinstance(display_name, str) else None,
            "source": source if isinstance(source, str) else None,
        }
