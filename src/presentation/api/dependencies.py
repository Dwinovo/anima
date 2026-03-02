from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from neo4j import AsyncDriver
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.cognition.decision_model import SocialDecisionModel
from src.application.cognition.langgraph_orchestrator import LangGraphDecisionOrchestrator
from src.application.cognition.orchestrator import AgentDecisionOrchestrator
from src.application.usecases.agent.register_agent import RegisterAgentUseCase
from src.application.usecases.agent.run_agent_decision import RunAgentDecisionUseCase
from src.application.usecases.agent.unregister_agent import UnregisterAgentUseCase
from src.application.usecases.event.report_event import ReportEventUseCase
from src.application.usecases.event.search_events import SearchEventsUseCase
from src.application.usecases.session.create_session import CreateSessionUseCase
from src.application.usecases.session.delete_session import DeleteSessionUseCase
from src.application.usecases.session.list_sessions import (
    ListSessionsUseCase,
)
from src.core.config import settings
from src.domain.agent.checkpoint_repository import AgentCheckpointRepository
from src.domain.agent.presence_repository import AgentPresenceRepository
from src.domain.agent.profile_repository import AgentProfileRepository
from src.domain.memory.event_payload_repository import EventPayloadRepository
from src.domain.memory.graph_event_repository import GraphEventRepository
from src.domain.session.repository import SessionRepository
from src.infrastructure.llm.social_agent import SocialAgent
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
from src.infrastructure.persistence.redis.checkpoint_repository import RedisCheckpointRepository
from src.infrastructure.persistence.redis.client import RedisClient
from src.infrastructure.persistence.redis.presence_repository import (
    RedisPresenceRepository,
)
from src.infrastructure.persistence.redis.profile_repository import RedisProfileRepository

# -----------------------------------------------------------------------------
# Redis (app-lifespan singletons -> request injection)
# -----------------------------------------------------------------------------


def get_redis_client(request: Request) -> RedisClient:
    # main.py lifespan: app.state.redis = RedisClient.from_url(...)
    """获取并返回对应的依赖或数据。"""
    return request.app.state.redis


def get_presence_repo(
    client: RedisClient = Depends(get_redis_client),
) -> AgentPresenceRepository:
    """获取并返回对应的依赖或数据。"""
    return RedisPresenceRepository(client)


def get_profile_repo(
    client: RedisClient = Depends(get_redis_client),
) -> AgentProfileRepository:
    """获取并返回对应的依赖或数据。"""
    return RedisProfileRepository(client)


def get_langgraph_checkpointer(request: Request) -> AsyncRedisSaver:
    """获取 LangGraph Redis Checkpointer。"""
    return request.app.state.langgraph_checkpointer


def get_checkpoint_repo(
    client: RedisClient = Depends(get_redis_client),
    checkpointer: AsyncRedisSaver = Depends(get_langgraph_checkpointer),
) -> AgentCheckpointRepository:
    """获取并返回对应的依赖或数据。"""
    return RedisCheckpointRepository(
        client,
        langgraph_checkpointer=checkpointer,
    )


# -----------------------------------------------------------------------------
# Mongo (app-lifespan singletons -> request injection)
# -----------------------------------------------------------------------------


def get_mongo_manager(request: Request) -> MongoManager:
    # main.py lifespan: app.state.mongo = MongoManager(...)
    """获取并返回对应的依赖或数据。"""
    return request.app.state.mongo


def get_event_payload_repo(
    manager: MongoManager = Depends(get_mongo_manager),
) -> EventPayloadRepository:
    """获取并返回对应的依赖或数据。"""
    return MongoEventPayloadRepository(manager.db)


# -----------------------------------------------------------------------------
# Postgres (engine/session_factory are app-lifespan; AsyncSession is request-scope)
# -----------------------------------------------------------------------------


def get_pg_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    # main.py lifespan: app.state.pg_session_factory = create_session_factory(engine)
    """获取并返回对应的依赖或数据。"""
    return request.app.state.pg_session_factory


async def get_pg_session(
    factory: async_sessionmaker[AsyncSession] = Depends(get_pg_session_factory),
) -> AsyncGenerator[AsyncSession, None]:
    """获取并返回对应的依赖或数据。"""
    async for session in get_session(factory):
        yield session


def get_session_repo(
    session: AsyncSession = Depends(get_pg_session),
) -> SessionRepository:
    """获取并返回对应的依赖或数据。"""
    return PostgresSessionRepository(session)


def get_create_session_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
) -> CreateSessionUseCase:
    """获取并返回对应的依赖或数据。"""
    return CreateSessionUseCase(session_repo, default_llm_model=settings.default_llm_model)


def get_delete_session_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
) -> DeleteSessionUseCase:
    """获取并返回对应的依赖或数据。"""
    return DeleteSessionUseCase(session_repo)


def get_list_sessions_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
) -> ListSessionsUseCase:
    """获取并返回对应的依赖或数据。"""
    return ListSessionsUseCase(session_repo)


def get_register_agent_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
    presence_repo: AgentPresenceRepository = Depends(get_presence_repo),
    profile_repo: AgentProfileRepository = Depends(get_profile_repo),
) -> RegisterAgentUseCase:
    """获取并返回对应的依赖或数据。"""
    return RegisterAgentUseCase(session_repo, presence_repo, profile_repo)


def get_unregister_agent_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
    presence_repo: AgentPresenceRepository = Depends(get_presence_repo),
    profile_repo: AgentProfileRepository = Depends(get_profile_repo),
    checkpoint_repo: AgentCheckpointRepository = Depends(get_checkpoint_repo),
) -> UnregisterAgentUseCase:
    """获取并返回对应的依赖或数据。"""
    return UnregisterAgentUseCase(session_repo, presence_repo, profile_repo, checkpoint_repo)


def get_neo4j_manager(request: Request) -> Neo4jManager:
    """获取并返回对应的依赖或数据。"""
    return request.app.state.neo4j


def get_neo4j_driver(
    manager: Neo4jManager = Depends(get_neo4j_manager),
) -> AsyncDriver:
    """获取并返回对应的依赖或数据。"""
    return manager.driver


def get_graph_event_repo(
    driver: AsyncDriver = Depends(get_neo4j_driver),
) -> GraphEventRepository:
    """获取并返回对应的依赖或数据。"""
    return Neo4jGraphEventRepository(driver)


def get_report_event_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
    event_payload_repo: EventPayloadRepository = Depends(get_event_payload_repo),
    graph_event_repo: GraphEventRepository = Depends(get_graph_event_repo),
) -> ReportEventUseCase:
    """获取并返回对应的依赖或数据。"""
    return ReportEventUseCase(session_repo, event_payload_repo, graph_event_repo)


def get_search_events_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
    event_payload_repo: EventPayloadRepository = Depends(get_event_payload_repo),
    graph_event_repo: GraphEventRepository = Depends(get_graph_event_repo),
) -> SearchEventsUseCase:
    """获取并返回对应的依赖或数据。"""
    return SearchEventsUseCase(session_repo, event_payload_repo, graph_event_repo)


def get_social_decision_model() -> SocialDecisionModel:
    """获取并返回对应的依赖或数据。"""
    return SocialAgent(
        model_name=settings.default_llm_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )


def get_agent_decision_orchestrator(
    profile_repo: AgentProfileRepository = Depends(get_profile_repo),
    checkpoint_repo: AgentCheckpointRepository = Depends(get_checkpoint_repo),
    checkpointer: AsyncRedisSaver = Depends(get_langgraph_checkpointer),
    search_usecase: SearchEventsUseCase = Depends(get_search_events_usecase),
    report_usecase: ReportEventUseCase = Depends(get_report_event_usecase),
    decision_model: SocialDecisionModel = Depends(get_social_decision_model),
) -> AgentDecisionOrchestrator:
    """获取并返回对应的依赖或数据。"""
    return LangGraphDecisionOrchestrator(
        profile_repo=profile_repo,
        checkpoint_repo=checkpoint_repo,
        search_usecase=search_usecase,
        report_usecase=report_usecase,
        decision_model=decision_model,
        checkpoint_ttl_seconds=settings.langgraph_checkpoint_ttl_seconds,
        working_memory_window=settings.langgraph_working_memory_window,
        checkpointer=checkpointer,
        checkpoint_namespace=settings.langgraph_checkpoint_namespace,
    )


def get_run_agent_decision_usecase(
    session_repo: SessionRepository = Depends(get_session_repo),
    presence_repo: AgentPresenceRepository = Depends(get_presence_repo),
    orchestrator: AgentDecisionOrchestrator = Depends(get_agent_decision_orchestrator),
) -> RunAgentDecisionUseCase:
    """获取并返回对应的依赖或数据。"""
    return RunAgentDecisionUseCase(
        session_repo=session_repo,
        presence_repo=presence_repo,
        orchestrator=orchestrator,
    )
