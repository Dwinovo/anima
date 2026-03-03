from __future__ import annotations

from src.application.dto.agent import AgentLifecycleResult
from src.core.exceptions import (
    AgentNotFoundException,
    AuthenticationFailedException,
    SessionNotFoundException,
)
from src.domain.agent.auth_state_repository import AgentAuthStateRepository
from src.domain.agent.profile_repository import AgentProfileRepository
from src.domain.agent.token_service import AgentTokenService
from src.domain.session.repository import SessionRepository


class RefreshAgentTokensUseCase:
    """刷新 Agent 访问令牌并执行重放防护。"""

    def __init__(
        self,
        session_repo: SessionRepository,
        profile_repo: AgentProfileRepository,
        auth_state_repo: AgentAuthStateRepository,
        token_service: AgentTokenService,
    ) -> None:
        """初始化对象并注入所需依赖。"""
        self._session_repo = session_repo
        self._profile_repo = profile_repo
        self._auth_state_repo = auth_state_repo
        self._token_service = token_service

    async def execute(
        self,
        *,
        session_id: str,
        agent_id: str,
        refresh_token: str,
    ) -> AgentLifecycleResult:
        """执行业务流程并返回新 token 对。"""
        session = await self._session_repo.get(session_id=session_id)
        if session is None:
            raise SessionNotFoundException(session_id)

        profile_json = await self._profile_repo.get(session_id=session_id, agent_id=agent_id)
        if profile_json is None:
            raise AgentNotFoundException(session_id=session_id, uuid=agent_id)

        claims = await self._token_service.parse_token(token=refresh_token)
        if claims.token_type != "refresh":
            raise AuthenticationFailedException("Refresh token required.")
        if claims.session_id != session_id or claims.agent_id != agent_id:
            raise AuthenticationFailedException("Token subject mismatch.")
        if claims.refresh_jti is None:
            raise AuthenticationFailedException("Invalid refresh token jti.")

        current_version = await self._auth_state_repo.ensure_token_version(
            session_id=session_id,
            agent_id=agent_id,
            initial_version=1,
        )
        if claims.token_version != current_version:
            raise AuthenticationFailedException("Token version mismatch.")

        consumed = await self._auth_state_repo.consume_refresh_jti(
            session_id=session_id,
            agent_id=agent_id,
            refresh_jti=claims.refresh_jti,
        )
        if not consumed:
            await self._auth_state_repo.revoke_all_refresh_jti(session_id=session_id, agent_id=agent_id)
            await self._auth_state_repo.bump_token_version(session_id=session_id, agent_id=agent_id)
            raise AuthenticationFailedException("Refresh token replay detected.")

        next_refresh_jti = await self._token_service.generate_refresh_jti()
        access_token = await self._token_service.issue_access_token(
            session_id=session_id,
            agent_id=agent_id,
            token_version=current_version,
        )
        next_refresh_token = await self._token_service.issue_refresh_token(
            session_id=session_id,
            agent_id=agent_id,
            token_version=current_version,
            refresh_jti=next_refresh_jti,
        )
        await self._auth_state_repo.store_refresh_jti(
            session_id=session_id,
            agent_id=agent_id,
            refresh_jti=next_refresh_jti,
            ttl_seconds=self._token_service.refresh_token_ttl_seconds,
        )
        return AgentLifecycleResult(
            session_id=session_id,
            agent_id=agent_id,
            active=True,
            token_type="Bearer",
            access_token=access_token,
            access_token_expires_in=self._token_service.access_token_ttl_seconds,
            refresh_token=next_refresh_token,
            refresh_token_expires_in=self._token_service.refresh_token_ttl_seconds,
        )
