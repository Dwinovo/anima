from __future__ import annotations

import json

from src.core.exceptions import EntityNotFoundException, SessionNotFoundException
from src.domain.entity.auth_state_repository import EntityAuthStateRepository
from src.domain.entity.presence_repository import EntityPresenceRepository
from src.domain.entity.profile_repository import EntityProfileRepository
from src.domain.session.repository import SessionRepository


class MaintainEntityPresenceUseCase:
    """维护 Entity 在线心跳与在线态。"""

    def __init__(
        self,
        session_repo: SessionRepository,
        profile_repo: EntityProfileRepository,
        presence_repo: EntityPresenceRepository,
        auth_state_repo: EntityAuthStateRepository,
    ) -> None:
        """初始化对象并注入所需依赖。"""
        self._session_repo = session_repo
        self._profile_repo = profile_repo
        self._presence_repo = presence_repo
        self._auth_state_repo = auth_state_repo

    async def on_connect(
        self,
        *,
        session_id: str,
        entity_id: str,
        heartbeat_ttl_seconds: int,
    ) -> None:
        """处理连接建立：校验资源并标记在线。"""
        session = await self._session_repo.get(session_id=session_id)
        if session is None:
            raise SessionNotFoundException(session_id)

        profile_json = await self._profile_repo.get(session_id=session_id, entity_id=entity_id)
        if profile_json is None:
            raise EntityNotFoundException(session_id=session_id, uuid=entity_id)

        await self._presence_repo.activate(session_id=session_id, entity_id=entity_id)
        await self._presence_repo.touch_heartbeat(
            session_id=session_id,
            entity_id=entity_id,
            ttl_seconds=heartbeat_ttl_seconds,
        )

    async def on_pong(
        self,
        *,
        session_id: str,
        entity_id: str,
        heartbeat_ttl_seconds: int,
    ) -> None:
        """处理心跳响应：刷新 TTL 并确保在线态。"""
        await self._presence_repo.activate(session_id=session_id, entity_id=entity_id)
        await self._presence_repo.touch_heartbeat(
            session_id=session_id,
            entity_id=entity_id,
            ttl_seconds=heartbeat_ttl_seconds,
        )

    async def on_disconnect(self, *, session_id: str, entity_id: str) -> None:
        """处理连接断开：删除 Entity 的全部 Redis 数据。"""
        profile_json = await self._profile_repo.get(session_id=session_id, entity_id=entity_id)
        display_name = self._extract_display_name(profile_json)
        if display_name is not None:
            await self._profile_repo.release_display_name(
                session_id=session_id,
                entity_id=entity_id,
                display_name=display_name,
            )
        await self._profile_repo.delete(session_id=session_id, entity_id=entity_id)
        await self._presence_repo.deactivate(session_id=session_id, entity_id=entity_id)
        await self._presence_repo.clear_heartbeat(session_id=session_id, entity_id=entity_id)
        await self._auth_state_repo.revoke_all_refresh_jti(session_id=session_id, entity_id=entity_id)
        await self._auth_state_repo.bump_token_version(session_id=session_id, entity_id=entity_id)

    @staticmethod
    def _extract_display_name(profile_json: str | None) -> str | None:
        """从 profile 载荷中提取展示名索引键。"""
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
