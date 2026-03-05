from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import TypeVar, cast

from fastapi import Depends, Header, Query, Request
from neo4j import AsyncDriver
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.usecases.entity.get_entity import GetEntityUseCase
from src.application.usecases.entity.get_entity_context import GetEntityContextUseCase
from src.application.usecases.entity.maintain_presence import MaintainEntityPresenceUseCase
from src.application.usecases.entity.patch_entity import PatchEntityUseCase
from src.application.usecases.entity.refresh_entity_tokens import RefreshEntityTokensUseCase
from src.application.usecases.entity.register_entity import RegisterEntityUseCase
from src.application.usecases.entity.unregister_entity import UnregisterEntityUseCase
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
from src.domain.entity.auth_state_repository import EntityAuthStateRepository
from src.domain.entity.presence_repository import EntityPresenceRepository
from src.domain.entity.profile_repository import EntityProfileRepository
from src.domain.entity.token_service import EntityTokenService, TokenClaims
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
) -> EntityPresenceRepository:
    """构建在线态仓储（请求级）。"""
    return RedisPresenceRepository(client)


def get_profile_repo(
    client: RedisClient = Depends(get_redis_client),
) -> EntityProfileRepository:
    """构建画像仓储（请求级）。"""
    return RedisProfileRepository(client)


def get_auth_state_repo(
    client: RedisClient = Depends(get_redis_client),
) -> EntityAuthStateRepository:
    """构建鉴权状态仓储（请求级）。"""
    return RedisAuthStateRepository(client)


def get_token_service(request: Request) -> EntityTokenService:
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


def get_register_entity_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
    presence_repo: EntityPresenceRepository = Depends(get_presence_repo),
    profile_repo: EntityProfileRepository = Depends(get_profile_repo),
    auth_state_repo: EntityAuthStateRepository = Depends(get_auth_state_repo),
    token_service: EntityTokenService = Depends(get_token_service),
) -> RegisterEntityUseCase:
    """构建注册 Entity 用例。"""
    return RegisterEntityUseCase(
        session_repo,
        presence_repo,
        profile_repo,
        auth_state_repo,
        token_service,
    )


def get_unregister_entity_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
    presence_repo: EntityPresenceRepository = Depends(get_presence_repo),
    profile_repo: EntityProfileRepository = Depends(get_profile_repo),
    auth_state_repo: EntityAuthStateRepository = Depends(get_auth_state_repo),
) -> UnregisterEntityUseCase:
    """构建卸载 Entity 用例。"""
    return UnregisterEntityUseCase(session_repo, presence_repo, profile_repo, auth_state_repo)


def get_get_entity_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
    presence_repo: EntityPresenceRepository = Depends(get_presence_repo),
    profile_repo: EntityProfileRepository = Depends(get_profile_repo),
) -> GetEntityUseCase:
    """构建查询 Entity 用例。"""
    return GetEntityUseCase(session_repo, presence_repo, profile_repo)


def get_patch_entity_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
    presence_repo: EntityPresenceRepository = Depends(get_presence_repo),
    profile_repo: EntityProfileRepository = Depends(get_profile_repo),
) -> PatchEntityUseCase:
    """构建编辑 Entity 用例。"""
    return PatchEntityUseCase(session_repo, presence_repo, profile_repo)


def get_maintain_entity_presence_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
    presence_repo: EntityPresenceRepository = Depends(get_presence_repo),
    profile_repo: EntityProfileRepository = Depends(get_profile_repo),
    auth_state_repo: EntityAuthStateRepository = Depends(get_auth_state_repo),
) -> MaintainEntityPresenceUseCase:
    """构建 Entity 在线心跳维护用例。"""
    return MaintainEntityPresenceUseCase(session_repo, profile_repo, presence_repo, auth_state_repo)


def get_refresh_entity_tokens_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
    profile_repo: EntityProfileRepository = Depends(get_profile_repo),
    auth_state_repo: EntityAuthStateRepository = Depends(get_auth_state_repo),
    token_service: EntityTokenService = Depends(get_token_service),
) -> RefreshEntityTokensUseCase:
    """构建刷新 Entity Token 用例。"""
    return RefreshEntityTokensUseCase(
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
    profile_repo: EntityProfileRepository = Depends(get_profile_repo),
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


def get_entity_context_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
    presence_repo: EntityPresenceRepository = Depends(get_presence_repo),
    profile_repo: EntityProfileRepository = Depends(get_profile_repo),
    event_payload_repo: EventPayloadRepository = Depends(get_event_payload_repo),
    graph_event_repo: GraphEventRepository = Depends(get_graph_event_repo),
) -> GetEntityContextUseCase:
    """构建 Entity 社交上下文用例。"""
    return GetEntityContextUseCase(
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
    expected_entity_id: str | None,
    token_service: EntityTokenService,
    auth_state_repo: EntityAuthStateRepository,
) -> TokenClaims:
    """解析并校验 access token 与 Redis token_version。"""
    claims = await token_service.parse_token(token=token)
    if claims.token_type != "access":
        raise AuthenticationFailedException("Access token required.")
    if claims.session_id != session_id:
        raise AuthenticationFailedException("Token session mismatch.")
    if expected_entity_id is not None and claims.entity_id != expected_entity_id:
        raise AuthenticationFailedException("Token subject mismatch.")
    current_version = await auth_state_repo.ensure_token_version(
        session_id=session_id,
        entity_id=claims.entity_id,
        initial_version=1,
    )
    if claims.token_version != current_version:
        raise AuthenticationFailedException("Token version mismatch.")
    return claims


async def require_entity_access_claims(
    session_id: str,
    entity_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
    token_service: EntityTokenService = Depends(get_token_service),
    auth_state_repo: EntityAuthStateRepository = Depends(get_auth_state_repo),
) -> TokenClaims:
    """校验 Entity 路径资源访问令牌并返回声明。"""
    token = _extract_bearer_token(authorization)
    return await _validate_access_claims(
        token=token,
        session_id=session_id,
        expected_entity_id=entity_id,
        token_service=token_service,
        auth_state_repo=auth_state_repo,
    )


async def require_session_access_claims(
    session_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
    token_service: EntityTokenService = Depends(get_token_service),
    auth_state_repo: EntityAuthStateRepository = Depends(get_auth_state_repo),
) -> TokenClaims:
    """校验 Session 级别访问令牌并返回声明。"""
    token = _extract_bearer_token(authorization)
    return await _validate_access_claims(
        token=token,
        session_id=session_id,
        expected_entity_id=None,
        token_service=token_service,
        auth_state_repo=auth_state_repo,
    )


@dataclass(slots=True)
class WsAccessClaimsResult:
    """WebSocket 鉴权结果。"""

    claims: TokenClaims | None
    error: AuthenticationFailedException | None = None


async def require_entity_ws_access_claims(
    session_id: str,
    entity_id: str,
    access_token: str | None = Query(default=None),
    token_service: EntityTokenService = Depends(get_token_service),
    auth_state_repo: EntityAuthStateRepository = Depends(get_auth_state_repo),
) -> WsAccessClaimsResult:
    """校验 WebSocket query access token，并返回可用于回包的结果对象。"""
    if access_token is None:
        return WsAccessClaimsResult(
            claims=None,
            error=AuthenticationFailedException("Missing access token."),
        )
    try:
        claims = await _validate_access_claims(
            token=access_token,
            session_id=session_id,
            expected_entity_id=entity_id,
            token_service=token_service,
            auth_state_repo=auth_state_repo,
        )
    except AuthenticationFailedException as exc:
        return WsAccessClaimsResult(claims=None, error=exc)
    return WsAccessClaimsResult(claims=claims, error=None)
