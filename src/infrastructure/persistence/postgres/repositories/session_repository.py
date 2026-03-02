# src/infrastructure/persistence/postgres/repositories/session_repository.py
from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.session.entities import Session
from src.domain.session.repository import SessionRepository
from src.infrastructure.persistence.postgres.models import SessionModel


class PostgresSessionRepository(SessionRepository):
    """PostgreSQL 控制面 sessions 仓储（Session 配置 + 配额锚点）。"""

    def __init__(self, session: AsyncSession) -> None:
        """初始化对象并注入所需依赖。"""
        self._session = session

    @staticmethod
    def _to_domain(model: SessionModel) -> Session:
        """执行 `_to_domain` 相关逻辑。"""
        return Session(
            session_id=model.session_id,
            name=model.name or model.session_id,
            description=model.description,
            max_agents_limit=model.max_agents_limit,
            default_llm=model.default_llm,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def list(self) -> list[Session]:
        """按稳定顺序列出全部会话配置。"""
        stmt = select(SessionModel).order_by(SessionModel.session_id.asc())
        models = (await self._session.scalars(stmt)).all()
        return [self._to_domain(model) for model in models]

    async def get(self, *, session_id: str) -> Session | None:
        """执行 `get` 相关逻辑。"""
        stmt = select(SessionModel).where(SessionModel.session_id == session_id)
        model = await self._session.scalar(stmt)
        if model is None:
            return None
        return self._to_domain(model)

    async def create(
        self,
        *,
        session_id: str,
        max_agents_limit: int,
        default_llm: str | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> Session:
        """创建资源并返回创建结果。"""
        model = SessionModel(
            session_id=session_id,
            max_agents_limit=max_agents_limit,
            default_llm=default_llm,
            name=name,
            description=description,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def update_quota(self, *, session_id: str, max_agents_limit: int) -> None:
        """更新目标资源的状态或字段。"""
        stmt = select(SessionModel).where(SessionModel.session_id == session_id)
        model = await self._session.scalar(stmt)
        if model is None:
            return
        model.max_agents_limit = max_agents_limit
        await self._session.commit()

    async def delete(self, *, session_id: str) -> None:
        """删除指定资源。"""
        await self._session.execute(delete(SessionModel).where(SessionModel.session_id == session_id))
        await self._session.commit()
