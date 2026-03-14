from __future__ import annotations

import json

from src.application.dto.entity import EntityLifecycleResult
from src.core.exceptions import EntityNotFoundException, SessionNotFoundException
from src.domain.entity.auth_state_repository import EntityAuthStateRepository
from src.domain.entity.presence_repository import EntityPresenceRepository
from src.domain.entity.profile_repository import EntityProfileRepository
from src.domain.session.repository import SessionRepository


class UnregisterEntityUseCase:
    """从指定 Session 卸载 Entity。"""

    def __init__(
        self,
        session_repo: SessionRepository,
        presence_repo: EntityPresenceRepository,
        profile_repo: EntityProfileRepository,
        auth_state_repo: EntityAuthStateRepository,
    ) -> None:
        """初始化对象并注入所需依赖。"""
        self._session_repo = session_repo
        self._presence_repo = presence_repo
        self._profile_repo = profile_repo
        self._auth_state_repo = auth_state_repo

    async def execute(self, *, session_id: str, entity_id: str) -> EntityLifecycleResult:
        """执行业务流程并返回结果。"""
        session = await self._session_repo.get(session_id=session_id)
        if session is None:
            raise SessionNotFoundException(session_id)

        is_active = await self._presence_repo.is_active(session_id=session_id, entity_id=entity_id)
        profile = await self._profile_repo.get(session_id=session_id, entity_id=entity_id)
        if not is_active and profile is None:
            raise EntityNotFoundException(session_id=session_id, uuid=entity_id)

        display_name = self._extract_display_name(profile)
        if display_name is not None:
            await self._profile_repo.release_display_name(
                session_id=session_id,
                entity_id=entity_id,
                display_name=display_name,
            )
        await self._presence_repo.deactivate(session_id=session_id, entity_id=entity_id)
        await self._presence_repo.clear_heartbeat(session_id=session_id, entity_id=entity_id)
        await self._profile_repo.delete(session_id=session_id, entity_id=entity_id)
        await self._auth_state_repo.revoke_all_refresh_jti(session_id=session_id, entity_id=entity_id)
        await self._auth_state_repo.bump_token_version(session_id=session_id, entity_id=entity_id)
        return EntityLifecycleResult(
            session_id=session_id,
            entity_id=entity_id,
            active=False,
        )

    @staticmethod
    def _extract_display_name(profile_json: str | None) -> str | None:
        """从既有 profile 缓存中提取 display_name。"""
        if profile_json is None:
            return None
        try:
            payload = json.loads(profile_json)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None
        display_name = payload.get("display_name")
        if isinstance(display_name, str) and display_name:
            return display_name
        return None
