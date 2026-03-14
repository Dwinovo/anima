from __future__ import annotations

import json

from src.application.dto.entity import EntityLifecycleResult
from src.core.exceptions import EntityNotFoundException, SessionNotFoundException
from src.domain.entity.presence_repository import EntityPresenceRepository
from src.domain.entity.profile_repository import EntityProfileRepository
from src.domain.session.repository import SessionRepository


class GetEntityUseCase:
    """查询指定 Entity 当前信息。"""

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

    async def execute(self, *, session_id: str, entity_id: str) -> EntityLifecycleResult:
        """执行业务流程并返回结果。"""
        session = await self._session_repo.get(session_id=session_id)
        if session is None:
            raise SessionNotFoundException(session_id)

        profile_json = await self._profile_repo.get(session_id=session_id, entity_id=entity_id)
        is_active = await self._presence_repo.is_active(session_id=session_id, entity_id=entity_id)
        if profile_json is None and not is_active:
            raise EntityNotFoundException(session_id=session_id, uuid=entity_id)

        parsed = self._parse_profile_payload(profile_json)
        return EntityLifecycleResult(
            session_id=session_id,
            entity_id=entity_id,
            active=is_active,
            name=parsed.get("name"),
            display_name=parsed.get("display_name"),
            source=parsed.get("source"),
        )

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

        name = payload.get("name")
        display_name = payload.get("display_name")
        source = payload.get("source")
        return {
            "name": name if isinstance(name, str) else None,
            "display_name": display_name if isinstance(display_name, str) else None,
            "source": source if isinstance(source, str) else None,
        }
