# Postgres Migrations

## 概述

本文件说明 Anima 当前的 PostgreSQL 迁移规则。当前 SQL 控制面只有 `sessions` 表，迁移系统由 Alembic 维护。

## 核心要点

- 所有表结构变更必须通过 Alembic 管理。
- 当前迁移 head 是 `20260306_0005_add_actions_to_sessions`。
- 当前迁移链：
  1. `20260302_0001_create_sessions_table`
  2. `20260303_0002_align_sessions_control_plane_schema`
  3. `20260304_0003_add_name_to_sessions`
  4. `20260305_0004_rename_max_agents_limit_to_max_entities_limit`
  5. `20260306_0005_add_actions_to_sessions`
- 常用命令：
  - `cd backend && uv run alembic current`
  - `cd backend && uv run alembic upgrade head`
  - `cd backend && uv run alembic downgrade -1`
  - `cd backend && uv run alembic revision --autogenerate -m "message"`

## 约束

- 禁止手工修改生产表结构。
- 模型变更必须伴随 `upgrade` 和 `downgrade` 对称迁移。
- 修改迁移或 ORM 模型后，应同步刷新 [数据库快照](../generated/db-schema.md)。
- 文档中的 migration head 必须与 `backend/alembic/versions/` 保持一致。

## 相关文件

- [../../backend/alembic.ini](../../backend/alembic.ini)
- [../../backend/alembic/versions/20260306_0005_add_actions_to_sessions.py](../../backend/alembic/versions/20260306_0005_add_actions_to_sessions.py)
- [../../backend/src/infrastructure/persistence/postgres/models.py](../../backend/src/infrastructure/persistence/postgres/models.py)
- [../generated/db-schema.md](../generated/db-schema.md)
