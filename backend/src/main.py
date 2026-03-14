# src/main.py
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from src.core.config import settings
from src.core.exceptions import AnimaException

# Mongo
from src.infrastructure.persistence.mongo.client import MongoManager
from src.infrastructure.persistence.neo4j.client import Neo4jManager

# Postgres
from src.infrastructure.persistence.postgres.database import create_engine, create_session_factory

# Redis
from src.infrastructure.persistence.redis.client import RedisClient
from src.infrastructure.security.hmac_token_service import HmacTokenService
from src.presentation.api.exception_handlers import (
    anima_exception_handler,
    http_exception_handler,
    request_validation_exception_handler,
)
from src.presentation.router import api_router

logger = logging.getLogger(__name__)


async def _check_redis_connection(redis: RedisClient) -> bool:
    """启动时检测 Redis 是否可连通。"""
    try:
        return await redis.ping()
    except Exception:
        logger.exception("Startup dependency check failed: redis is unavailable.")
        return False


async def _check_mongo_connection(mongo: MongoManager) -> bool:
    """启动时检测 MongoDB 是否可连通。"""
    try:
        return await mongo.ping()
    except Exception:
        logger.exception("Startup dependency check failed: mongo is unavailable.")
        return False


async def _check_postgres_connection(pg_engine: AsyncEngine) -> bool:
    """启动时检测 PostgreSQL 是否可连通。"""
    try:
        async with pg_engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("Startup dependency check failed: postgres is unavailable.")
        return False


async def _check_neo4j_connection(neo4j: Neo4jManager) -> bool:
    """启动时检测 Neo4j 是否可连通并尝试初始化 schema。"""
    try:
        await neo4j.ensure_schema()
        return True
    except Exception:
        logger.exception("Startup dependency check failed: neo4j is unavailable.")
        return False


async def _run_startup_dependency_checks(
    *,
    redis: RedisClient,
    mongo: MongoManager,
    pg_engine: AsyncEngine,
    neo4j: Neo4jManager,
) -> dict[str, bool]:
    """执行启动依赖连通性检查，失败仅记录日志，不阻断服务启动。"""
    results = {
        "redis": await _check_redis_connection(redis),
        "mongo": await _check_mongo_connection(mongo),
        "postgres": await _check_postgres_connection(pg_engine),
        "neo4j": await _check_neo4j_connection(neo4j),
    }
    failed = [name for name, ok in results.items() if not ok]
    if failed:
        logger.error(
            "Startup dependency checks failed for: %s; service will continue running.",
            ", ".join(failed),
        )
    return results


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """管理应用生命周期内的资源初始化与释放。"""
    # 1) Redis（单例）
    app.state.redis = RedisClient.from_url(settings.redis_url)
    app.state.token_service = HmacTokenService(
        secret=settings.auth_token_secret,
        access_token_ttl_seconds=settings.auth_access_token_ttl_seconds,
        refresh_token_ttl_seconds=settings.auth_refresh_token_ttl_seconds,
    )

    # 2) Mongo（单例）
    app.state.mongo = MongoManager(settings.mongo_url, settings.mongo_database)

    # 3) Postgres（单例：engine + session_factory）
    engine = create_engine(settings.database_url)
    app.state.pg_engine = engine
    app.state.pg_session_factory = create_session_factory(engine)

    app.state.neo4j = Neo4jManager(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    await _run_startup_dependency_checks(
        redis=app.state.redis,
        mongo=app.state.mongo,
        pg_engine=app.state.pg_engine,
        neo4j=app.state.neo4j,
    )
    try:
        yield
    finally:
        # 关闭顺序：先关请求层依赖外的资源
        await app.state.redis.close()
        await app.state.mongo.close()
        await app.state.pg_engine.dispose()
        await app.state.neo4j.close()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods_list,
    allow_headers=settings.cors_allow_headers_list,
)
app.include_router(api_router)
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(AnimaException, anima_exception_handler)
app.add_exception_handler(Exception, http_exception_handler)
