# Backend Root Restructure Design

## 概述

本设计将当前仓库从“根目录同时承载文档和 Python 工程”的布局，重构为“根目录以仓库文档为主，完整服务端工程收敛到 `backend/`”的布局。额外约束是 `.env` 保留在仓库根目录，避免本地运行习惯被完全打断。

## 核心要点

- 目标结构
  - 根目录保留：`docs/`、`backend/`、`.env`、`.gitignore`、`AGENTS.md`、`ARCHITECTURE.md`、`LICENSE`
  - `backend/` 收纳：`backend/src/`、`backend/tests/`、`backend/alembic/`、`backend/pyproject.toml`、`backend/uv.lock`、`backend/.python-version`、`backend/alembic.ini`、`backend/.env.example`
- Python 包结构不变
  - 仍使用 `src.*` 导入路径
  - 只是把工程根从仓库根切换为 `backend/`
- 命令入口统一
  - 后续文档命令统一改成从 `backend/` 执行，如 `cd backend && uv run pytest -q`
  - Alembic、ruff、pytest 都以 `backend/` 为工作目录
- 环境变量策略
  - `.env` 继续放在仓库根目录
  - `backend/src/core/config.py` 需要显式向上兼容根目录 `.env`

## 约束

- 不重命名 Python 包，不拆分模块，不做无关业务改动。
- 所有文档路径都要同步更新，避免 Agent 再被旧的根目录布局误导。
- `backend/` 必须成为完整可运行的 Python 工程根。
- `docs/` 中 active plan、architecture、agents 索引必须同步反映新路径。

## 风险

- `backend/alembic.ini` 与迁移脚本的相对路径配置可能受目录变化影响。
- `backend/pyproject.toml` 下沉后，`uv`、pytest、ruff 的执行目录必须跟着调整。
- 若 `pydantic-settings` 默认只查当前目录 `.env`，则移动后可能丢失根目录环境文件。

## 验证标准

- 在 `backend/` 下执行 `uv run ruff check src tests` 通过
- 在 `backend/` 下执行 `uv run pytest -q` 通过
- 旧根目录路径引用在文档中不再残留
- `AGENTS.md` 与 `ARCHITECTURE.md` 能准确描述新结构

## 相关文件

- [../../../AGENTS.md](../../../AGENTS.md)
- [../../../ARCHITECTURE.md](../../../ARCHITECTURE.md)
- [./index.md](./index.md)
- [../completed/2026-03-14-agent-first-repo-restructure.md](../completed/2026-03-14-agent-first-repo-restructure.md)
