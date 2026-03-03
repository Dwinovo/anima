# src/infrastructure/persistence/postgres/models.py
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.postgres.base import Base


class SessionModel(Base):
    """Session 控制面 ORM 模型。"""

    __tablename__ = "sessions"

    # 多租户锚点：session_id 作为主键
    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)

    # Session 名称（管理面板展示名）
    name: Mapped[str] = mapped_column(String(128), nullable=False)

    # Session 描述（全局 context）
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 配额控制：max_agents_limit（非常关键）
    max_agents_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    # 审计字段
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
