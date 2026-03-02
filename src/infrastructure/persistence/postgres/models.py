# src/infrastructure/persistence/postgres/models.py
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.postgres.base import Base


class SessionModel(Base):
    __tablename__ = "sessions"

    # 多租户锚点：session_id 作为主键
    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)

    # 可选：Session 名称/描述（全局 context）
    name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 配额控制：max_agents_limit（非常关键）
    max_agents_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    # 默认 LLM（可按你们枚举/字符串）
    default_llm: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # 审计字段
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )
