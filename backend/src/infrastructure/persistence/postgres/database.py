# src/infrastructure/persistence/postgres/database.py
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_engine(database_url: str) -> AsyncEngine:
    # 你可以按需加 pool_size/max_overflow/pool_recycle
    """创建数据库异步引擎。"""
    return create_async_engine(
        database_url,
        pool_pre_ping=True,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """创建数据库会话工厂。"""
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,  # 常用：避免 commit 后对象过期
        autoflush=False,
    )


async def get_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """提供请求级数据库会话。"""
    async with session_factory() as session:
        yield session