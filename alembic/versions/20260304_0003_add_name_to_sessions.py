"""add name to sessions

Revision ID: 20260304_0003
Revises: 20260303_0002
Create Date: 2026-03-04 10:30:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260304_0003"
down_revision: str | None = "20260303_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """执行数据库升级迁移。"""
    op.add_column("sessions", sa.Column("name", sa.String(length=128), nullable=True))
    op.execute("UPDATE sessions SET name = session_id WHERE name IS NULL OR name = ''")
    with op.batch_alter_table("sessions") as batch_op:
        batch_op.alter_column(
            "name",
            existing_type=sa.String(length=128),
            nullable=False,
        )


def downgrade() -> None:
    """执行数据库回滚迁移。"""
    with op.batch_alter_table("sessions") as batch_op:
        batch_op.drop_column("name")

