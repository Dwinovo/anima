"""add actions to sessions

Revision ID: 20260306_0005
Revises: 20260305_0004
Create Date: 2026-03-06 16:10:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260306_0005"
down_revision: str | None = "20260305_0004"
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
    if "actions" not in columns:
        with op.batch_alter_table("sessions") as batch_op:
            batch_op.add_column(
                sa.Column(
                    "actions",
                    sa.JSON(),
                    nullable=False,
                    server_default=sa.text("'[]'"),
                )
            )


def downgrade() -> None:
    """执行数据库回滚迁移。"""
    columns = _list_session_columns()
    if "actions" in columns:
        with op.batch_alter_table("sessions") as batch_op:
            batch_op.drop_column("actions")
