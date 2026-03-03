"""align sessions control plane schema

Revision ID: 20260303_0002
Revises: 20260302_0001
Create Date: 2026-03-03 20:00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260303_0002"
down_revision: str | None = "20260302_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """执行数据库升级迁移。"""
    # 先补齐历史空值，确保后续 updated_at 可以收敛为非空字段。
    op.execute("UPDATE sessions SET updated_at = created_at WHERE updated_at IS NULL")

    with op.batch_alter_table("sessions") as batch_op:
        batch_op.drop_column("name")
        batch_op.drop_column("default_llm")
        batch_op.alter_column(
            "updated_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        )


def downgrade() -> None:
    """执行数据库回滚迁移。"""
    with op.batch_alter_table("sessions") as batch_op:
        batch_op.add_column(sa.Column("default_llm", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("name", sa.String(length=128), nullable=True))
        batch_op.alter_column(
            "updated_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=True,
            server_default=None,
        )
