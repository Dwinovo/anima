"""rename max_agents_limit to max_entities_limit

Revision ID: 20260305_0004
Revises: 20260304_0003
Create Date: 2026-03-05 16:30:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260305_0004"
down_revision: str | None = "20260304_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _list_session_columns() -> set[str]:
    """读取 sessions 表列名集合。"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns("sessions")}


def upgrade() -> None:
    """执行数据库升级迁移。"""
    columns = _list_session_columns()
    if "max_agents_limit" in columns and "max_entities_limit" not in columns:
        with op.batch_alter_table("sessions") as batch_op:
            batch_op.alter_column(
                "max_agents_limit",
                new_column_name="max_entities_limit",
                existing_type=sa.Integer(),
                existing_nullable=False,
                existing_server_default=sa.text("100"),
            )


def downgrade() -> None:
    """执行数据库回滚迁移。"""
    columns = _list_session_columns()
    if "max_entities_limit" in columns and "max_agents_limit" not in columns:
        with op.batch_alter_table("sessions") as batch_op:
            batch_op.alter_column(
                "max_entities_limit",
                new_column_name="max_agents_limit",
                existing_type=sa.Integer(),
                existing_nullable=False,
                existing_server_default=sa.text("100"),
            )
