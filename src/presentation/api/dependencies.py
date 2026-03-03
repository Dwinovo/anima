from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TypeVar, cast

from fastapi import Depends, Header, Request
from neo4j import AsyncDriver
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.usecases.agent.get_agent import GetAgentUseCase
from src.application.usecases.agent.get_agent_context import GetAgentContextUseCase
from src.application.usecases.agent.maintain_presence import MaintainAgentPresenceUseCase
from src.application.usecases.agent.patch_agent import PatchAgentUseCase
from src.application.usecases.agent.refresh_agent_tokens import RefreshAgentTokensUseCase
from src.application.usecases.agent.register_agent import RegisterAgentUseCase
from src.application.usecases.agent.unregister_agent import UnregisterAgentUseCase
from src.application.usecases.event.list_session_events import ListSessionEventsUseCase
from src.application.usecases.event.report_event import ReportEventUseCase
from src.application.usecases.session.create_session import CreateSessionUseCase
from src.application.usecases.session.delete_session import DeleteSessionUseCase
from src.application.usecases.session.get_session import GetSessionUseCase
from src.application.usecases.session.list_sessions import (
    ListSessionsUseCase,
)
from src.application.usecases.session.patch_session import PatchSessionUseCase
from src.core.exceptions import AuthenticationFailedException
from src.domain.agent.auth_state_repository import AgentAuthStateRepository
from src.domain.agent.presence_repository import AgentPresenceRepository
from src.domain.agent.profile_repository import AgentProfileRepository
from src.domain.agent.token_service import AgentTokenService, TokenClaims
from src.domain.memory.event_payload_repository import EventPayloadRepository
from src.domain.memory.graph_event_repository import GraphEventRepository
from src.domain.session.repository import SessionRepository
from src.infrastructure.persistence.mongo.client import MongoManager
from src.infrastructure.persistence.mongo.event_payload_repository import (
    MongoEventPayloadRepository,
)
from src.infrastructure.persistence.neo4j.client import Neo4jManager
from src.infrastructure.persistence.neo4j.graph_event_repository import (
    Neo4jGraphEventRepository,
)
from src.infrastructure.persistence.postgres.database import get_session
from src.infrastructure.persistence.postgres.repositories.session_repository import PostgresSessionRepository
from src.infrastructure.persistence.redis.auth_state_repository import (
    RedisAuthStateRepository,
)
from src.infrastructure.persistence.redis.client import RedisClient
from src.infrastructure.persistence.redis.presence_repository import (
    RedisPresenceRepository,
)
from src.infrastructure.persistence.redis.profile_repository import RedisProfileRepository

# -----------------------------------------------------------------------------
# Redis (app-lifespan singletons -> request injection)
# -----------------------------------------------------------------------------


TAppState = TypeVar("TAppState")


def _get_app_state(request: Request, attr_name: str) -> TAppState:
    """读取应用生命周期内初始化的 `app.state` 资源。"""
    value = getattr(request.app.state, attr_name, None)
    if value is None:
        raise RuntimeError(f"Application state '{attr_name}' is not initialized.")
    return cast(TAppState, value)


def get_redis_client(request: Request) -> RedisClient:
    """获取 Redis 客户端（应用级单例）。"""
    return _get_app_state(request, "redis")


def get_presence_repo(
    client: RedisClient = Depends(get_redis_client),
) -> AgentPresenceRepository:
    """构建在线态仓储（请求级）。"""
    return RedisPresenceRepository(client)


def get_profile_repo(
    client: RedisClient = Depends(get_redis_client),
) -> AgentProfileRepository:
    """构建画像仓储（请求级）。"""
    return RedisProfileRepository(client)


def get_auth_state_repo(
    client: RedisClient = Depends(get_redis_client),
) -> AgentAuthStateRepository:
    """构建鉴权状态仓储（请求级）。"""
    return RedisAuthStateRepository(client)


def get_token_service(request: Request) -> AgentTokenService:
    """获取 Token 服务（应用级单例）。"""
    return _get_app_state(request, "token_service")


# -----------------------------------------------------------------------------
# Mongo (app-lifespan singletons -> request injection)
# -----------------------------------------------------------------------------


def get_mongo_manager(request: Request) -> MongoManager:
    """获取 Mongo 管理器（应用级单例）。"""
    return _get_app_state(request, "mongo")


def get_event_payload_repo(
    manager: MongoManager = Depends(get_mongo_manager),
) -> EventPayloadRepository:
    """构建事件载荷仓储（请求级）。"""
    return MongoEventPayloadRepository(manager.db)


# -----------------------------------------------------------------------------
# Postgres (engine/session_factory are app-lifespan; AsyncSession is request-scope)
# -----------------------------------------------------------------------------


def get_pg_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    """获取 PostgreSQL Session 工厂（应用级单例）。"""
    return _get_app_state(request, "pg_session_factory")


async def get_pg_session(
    factory: async_sessionmaker[AsyncSession] = Depends(get_pg_session_factory),
) -> AsyncGenerator[AsyncSession, None]:
    """提供请求级 `AsyncSession`。"""
    async for session in get_session(factory):
        yield session


def get_session_repo(
    session: AsyncSession = Depends(get_pg_session),
) -> SessionRepository:
    """构建 Session 仓储（请求级）。"""
    return PostgresSessionRepository(session)


def get_create_session_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
) -> CreateSessionUseCase:
    """构建创建 Session 用例。"""
    return CreateSessionUseCase(session_repo)


def get_delete_session_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
) -> DeleteSessionUseCase:
    """构建删除 Session 用例。"""
    return DeleteSessionUseCase(session_repo)


def get_list_sessions_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
) -> ListSessionsUseCase:
    """构建列出 Session 用例。"""
    return ListSessionsUseCase(session_repo)


def get_get_session_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
) -> GetSessionUseCase:
    """构建查询 Session 详情用例。"""
    return GetSessionUseCase(session_repo)


def get_patch_session_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
) -> PatchSessionUseCase:
    """构建更新 Session 用例。"""
    return PatchSessionUseCase(session_repo)


def get_register_agent_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
    presence_repo: AgentPresenceRepository = Depends(get_presence_repo),
    profile_repo: AgentProfileRepository = Depends(get_profile_repo),
    auth_state_repo: AgentAuthStateRepository = Depends(get_auth_state_repo),
    token_service: AgentTokenService = Depends(get_token_service),
) -> RegisterAgentUseCase:
    """构建注册 Agent 用例。"""
    return RegisterAgentUseCase(
        session_repo,
        presence_repo,
        profile_repo,
        auth_state_repo,
        token_service,
    )


def get_unregister_agent_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
    presence_repo: AgentPresenceRepository = Depends(get_presence_repo),
    profile_repo: AgentProfileRepository = Depends(get_profile_repo),
    auth_state_repo: AgentAuthStateRepository = Depends(get_auth_state_repo),
) -> UnregisterAgentUseCase:
    """构建卸载 Agent 用例。"""
    return UnregisterAgentUseCase(session_repo, presence_repo, profile_repo, auth_state_repo)


def get_get_agent_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
    presence_repo: AgentPresenceRepository = Depends(get_presence_repo),
    profile_repo: AgentProfileRepository = Depends(get_profile_repo),
) -> GetAgentUseCase:
    """构建查询 Agent 用例。"""
    return GetAgentUseCase(session_repo, presence_repo, profile_repo)


def get_patch_agent_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
    presence_repo: AgentPresenceRepository = Depends(get_presence_repo),
    profile_repo: AgentProfileRepository = Depends(get_profile_repo),
) -> PatchAgentUseCase:
    """构建编辑 Agent 用例。"""
    return PatchAgentUseCase(session_repo, presence_repo, profile_repo)


def get_maintain_agent_presence_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
    presence_repo: AgentPresenceRepository = Depends(get_presence_repo),
    profile_repo: AgentProfileRepository = Depends(get_profile_repo),
    auth_state_repo: AgentAuthStateRepository = Depends(get_auth_state_repo),
) -> MaintainAgentPresenceUseCase:
    """构建 Agent 在线心跳维护用例。"""
    return MaintainAgentPresenceUseCase(session_repo, profile_repo, presence_repo, auth_state_repo)


def get_refresh_agent_tokens_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
    profile_repo: AgentProfileRepository = Depends(get_profile_repo),
    auth_state_repo: AgentAuthStateRepository = Depends(get_auth_state_repo),
    token_service: AgentTokenService = Depends(get_token_service),
) -> RefreshAgentTokensUseCase:
    """构建刷新 Agent Token 用例。"""
    return RefreshAgentTokensUseCase(
        session_repo,
        profile_repo,
        auth_state_repo,
        token_service,
    )


def get_neo4j_manager(request: Request) -> Neo4jManager:
    """获取 Neo4j 管理器（应用级单例）。"""
    return _get_app_state(request, "neo4j")


def get_neo4j_driver(
    manager: Neo4jManager = Depends(get_neo4j_manager),
) -> AsyncDriver:
    """获取 Neo4j 异步驱动。"""
    return manager.driver


def get_graph_event_repo(
    driver: AsyncDriver = Depends(get_neo4j_driver),
) -> GraphEventRepository:
    """构建图谱事件仓储（请求级）。"""
    return Neo4jGraphEventRepository(driver)


def get_report_event_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
    profile_repo: AgentProfileRepository = Depends(get_profile_repo),
    event_payload_repo: EventPayloadRepository = Depends(get_event_payload_repo),
    graph_event_repo: GraphEventRepository = Depends(get_graph_event_repo),
) -> ReportEventUseCase:
    """构建事件上报用例。"""
    return ReportEventUseCase(session_repo, profile_repo, event_payload_repo, graph_event_repo)


def get_list_session_events_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
    event_payload_repo: EventPayloadRepository = Depends(get_event_payload_repo),
    graph_event_repo: GraphEventRepository = Depends(get_graph_event_repo),
) -> ListSessionEventsUseCase:
    """构建会话事件列表用例。"""
    return ListSessionEventsUseCase(session_repo, event_payload_repo, graph_event_repo)


def get_agent_context_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
    presence_repo: AgentPresenceRepository = Depends(get_presence_repo),
    profile_repo: AgentProfileRepository = Depends(get_profile_repo),
    event_payload_repo: EventPayloadRepository = Depends(get_event_payload_repo),
    graph_event_repo: GraphEventRepository = Depends(get_graph_event_repo),
) -> GetAgentContextUseCase:
    """构建 Agent 社交上下文用例。"""
    return GetAgentContextUseCase(
        session_repo,
        presence_repo,
        profile_repo,
        event_payload_repo,
        graph_event_repo,
    )


def _extract_bearer_token(authorization: str | None) -> str:
    """从 Authorization 请求头提取 Bearer Token。"""
    if authorization is None:
        raise AuthenticationFailedException("Missing Authorization header.")
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise AuthenticationFailedException("Authorization must be Bearer token.")
    token = authorization[len(prefix) :].strip()
    if not token:
        raise AuthenticationFailedException("Empty bearer token.")
    return token


async def _validate_access_claims(
    *,
    token: str,
    session_id: str,
    expected_agent_id: str | None,
    token_service: AgentTokenService,
    auth_state_repo: AgentAuthStateRepository,
) -> TokenClaims:
    """解析并校验 access token 与 Redis token_version。"""
    claims = await token_service.parse_token(token=token)
    if claims.token_type != "access":
        raise AuthenticationFailedException("Access token required.")
    if claims.session_id != session_id:
        raise AuthenticationFailedException("Token session mismatch.")
    if expected_agent_id is not None and claims.agent_id != expected_agent_id:
        raise AuthenticationFailedException("Token subject mismatch.")
    current_version = await auth_state_repo.ensure_token_version(
        session_id=session_id,
        agent_id=claims.agent_id,
        initial_version=1,
    )
    if claims.token_version != current_version:
        raise AuthenticationFailedException("Token version mismatch.")
    return claims


async def require_agent_access_claims(
    session_id: str,
    agent_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
    token_service: AgentTokenService = Depends(get_token_service),
    auth_state_repo: AgentAuthStateRepository = Depends(get_auth_state_repo),
) -> TokenClaims:
    """校验 Agent 路径资源访问令牌并返回声明。"""
    token = _extract_bearer_token(authorization)
    return await _validate_access_claims(
        token=token,
        session_id=session_id,
        expected_agent_id=agent_id,
        token_service=token_service,
        auth_state_repo=auth_state_repo,
    )


async def require_session_access_claims(
    session_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
    token_service: AgentTokenService = Depends(get_token_service),
    auth_state_repo: AgentAuthStateRepository = Depends(get_auth_state_repo),
) -> TokenClaims:
    """校验 Session 级别访问令牌并返回声明。"""
    token = _extract_bearer_token(authorization)
    return await _validate_access_claims(
        token=token,
        session_id=session_id,
        expected_agent_id=None,
        token_service=token_service,
        auth_state_repo=auth_state_repo,
    )


async def validate_agent_access_token(
    *,
    token: str,
    session_id: str,
    agent_id: str,
    token_service: AgentTokenService,
    auth_state_repo: AgentAuthStateRepository,
) -> TokenClaims:
    """校验 WebSocket query token。"""
    return await _validate_access_claims(
        token=token,
        session_id=session_id,
        expected_agent_id=agent_id,
        token_service=token_service,
        auth_state_repo=auth_state_repo,
    )
