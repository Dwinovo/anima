# src/infrastructure/persistence/postgres/repositories/session_repository.py
from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.session.actions import SessionAction, session_actions_from_payload, session_actions_to_payload
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
            name=model.name,
            description=model.description,
            max_entities_limit=model.max_entities_limit,
            actions=session_actions_from_payload(model.actions),
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
        name: str,
        max_entities_limit: int,
        actions: tuple[SessionAction, ...],
        description: str | None = None,
    ) -> Session:
        """创建资源并返回创建结果。"""
        payload: dict[str, object] = {
            "session_id": session_id,
            "name": name,
            "max_entities_limit": max_entities_limit,
            "description": description,
            "actions": session_actions_to_payload(actions),
        }
        model = SessionModel(**payload)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def update_quota(self, *, session_id: str, max_entities_limit: int) -> None:
        """更新目标资源的状态或字段。"""
        stmt = select(SessionModel).where(SessionModel.session_id == session_id)
        model = await self._session.scalar(stmt)
        if model is None:
            return
        model.max_entities_limit = max_entities_limit
        await self._session.commit()

    async def delete(self, *, session_id: str) -> None:
        """删除指定资源。"""
        await self._session.execute(delete(SessionModel).where(SessionModel.session_id == session_id))
        await self._session.commit()

    async def update(
        self,
        *,
        session_id: str,
        name: str | None = None,
        description: str | None = None,
        max_entities_limit: int | None = None,
        actions: tuple[SessionAction, ...] | None = None,
    ) -> Session | None:
        """更新指定会话并返回最新实体。"""
        stmt = select(SessionModel).where(SessionModel.session_id == session_id)
        model = await self._session.scalar(stmt)
        if model is None:
            return None

        if name is not None:
            model.name = name
        if description is not None:
            model.description = description
        if max_entities_limit is not None:
            model.max_entities_limit = max_entities_limit
        if actions is not None:
            model.actions = session_actions_to_payload(actions)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_domain(model)
