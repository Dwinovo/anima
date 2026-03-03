# src/main.py
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

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
