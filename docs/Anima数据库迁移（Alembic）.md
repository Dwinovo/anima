# Anima 数据库迁移（Alembic）

本文档定义 Anima 项目中 PostgreSQL 结构迁移的标准流程。

## 1. 目标

- 所有表结构变更必须通过 Alembic 管理。
- 禁止手工在生产环境直接改表。
- 迁移脚本必须可回滚（`downgrade`）。

## 2. 当前结构

- Alembic 配置文件：`alembic.ini`
- 迁移目录：`alembic/`
- 版本脚本目录：`alembic/versions/`

## 3. 常用命令

在项目根目录执行：

```bash
cd /Users/wuwansheng/Project/anima
```

查看当前版本：

```bash
uv run alembic current
```

升级到最新版本：

```bash
uv run alembic upgrade head
```

回滚一个版本：

```bash
uv run alembic downgrade -1
```

生成新迁移（自动比较模型）：

```bash
uv run alembic revision --autogenerate -m "your message"
```

手工生成空迁移：

```bash
uv run alembic revision -m "your message"
```

## 4. 当前迁移链

当前版本迁移链如下：

1. `20260302_0001_create_sessions_table`
2. `20260303_0002_align_sessions_control_plane_schema`
3. `20260304_0003_add_name_to_sessions`（当前 `head`）

说明：

- 当前 `sessions` 控制面字段以 `head` 为准（包含 `name`）。
- 部署前建议执行 `uv run alembic current` 校验版本，确保处于最新 `head`。

## 5. 团队规范

- 每次合并涉及模型变更的代码，必须同时提交迁移脚本。
- 迁移脚本命名要体现业务意图（如 `create_sessions_table`）。
- `upgrade` 与 `downgrade` 必须保持对称。
