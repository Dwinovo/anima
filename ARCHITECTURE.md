# Architecture

## 概述

Anima 当前是一个单仓管理的前后端项目：`backend/` 承载 Entity Activity Network 后端内核，`apps/admin/` 承载管理台控制面。

仓库层面上，完整 Python 工程位于 `backend/`，管理台前端位于 `apps/admin/`；根目录主要保留文档入口、仓库说明和根级 `.env`。

## 模块地图

- `apps/admin/`
  - Next.js 16 + React 19 的管理台前端。
  - `app/` 使用 App Router；`layout.tsx` 已接入全局 Sidebar，并先提供 `overview` 和 `sessions` 两个空白占位模块。
  - UI 风格基线使用 neobrutalism 组件体系。
  - 通过 HTTP 调用 `backend/src/presentation/` 暴露的 `/api/v1` 接口，不直接依赖 Python 源码。
- `backend/src/main.py`
  - FastAPI 应用入口。
  - 初始化 Redis、MongoDB、Postgres、Neo4j。
  - 在启动阶段做依赖连通性检查，但失败时只记录日志，不阻断启动。
- `backend/src/presentation/`
  - `router.py` 聚合 `/api/v1` 路由。
  - `api/v1/*.py` 提供 Session、Entity、Event 的 HTTP / WebSocket 入口。
  - `api/schemas/` 定义请求与响应模型。
  - `api/dependencies.py` 是组合根：把基础设施实现装配到应用层用例。
- `backend/src/application/`
  - `usecases/session/*` 处理 Session 控制面。
  - `usecases/entity/*` 处理注册、查询、改名、下线、在线态和 token 刷新。
  - `usecases/event/*` 处理事件上报与列表查询。
  - `dto/*` 提供跨层返回对象。
- `backend/src/domain/`
  - `session/` 定义 Session 实体、动作约束和仓储协议。
  - `entity/` 定义在线态、画像、鉴权状态、token 服务协议。
  - `memory/` 定义事件载荷与图谱事件仓储协议。
- `backend/src/infrastructure/`
  - `persistence/postgres/` 保存 Session 控制面。
  - `persistence/redis/` 保存在线态、运行态、展示名索引、token 状态。
  - `persistence/mongo/` 保存 Event 完整载荷。
  - `persistence/neo4j/` 保存 Event 图谱骨架与查询索引。
  - `security/hmac_token_service.py` 实现 access / refresh token。
  - `observability/` 预留日志与指标接入点。
- `backend/src/core/`
  - `config.py` 管理运行配置。
  - `exceptions.py` 定义跨层错误语义。
- `backend/.env.example`
  - 提供环境变量样例。
  - 实际本地运行默认读取根目录 `.env`。
- `backend/tests/`
  - `architecture/` 验证架构边界。
  - `presentation/` 验证公开 API 暴露面与 schema。
  - `usecases/` 验证业务编排规则。
  - `infrastructure/` 与 `core/` 验证键名、Neo4j schema、启动检查等基础行为。

## 分层规则

- 允许的依赖方向：
  - `apps/admin` 可以依赖自己的 TypeScript 模块、静态资源和公开 API 契约文档。
  - 管理台与后端之间的边界是 HTTP API；共享的是资源词汇和契约，不是运行时代码。
  - `backend/src/presentation` 可以依赖 `backend/src/application`、`backend/src/core`。
  - `backend/src/presentation/api/dependencies.py` 作为组合根，可以装配 `backend/src/infrastructure` 实现。
  - `backend/src/application` 可以依赖 `backend/src/domain`、`backend/src/core`。
  - `backend/src/infrastructure` 可以依赖 `backend/src/domain` 协议、`backend/src/core` 配置与异常。
- 明确禁止的依赖方向：
  - `apps/admin` 不得直接耦合 Postgres、Redis、MongoDB、Neo4j 的内部结构，也不要导入 `backend/src/` 中的私有实现约定。
  - `backend/src/domain` 不得依赖 FastAPI、Pydantic、SQLAlchemy、Redis、Motor、Neo4j 驱动。
  - `backend/src/application` 不得直接依赖路由层或具体数据库 SDK。
  - `backend/src/infrastructure` 不得反向依赖 `backend/src/presentation`。
  - 路由处理函数不得自己写持久化逻辑；只能调用 use case。
- 当前兼容性约束：
  - API 仍使用 `/entities` 作为资源名，但领域上按 `Entity` 抽象理解。
  - `Session.actions` 只保留 `verb`、`description`、`details_schema`。

## 关键路径

### 1. 管理台控制面请求

- 入口：浏览器访问 `apps/admin/app/*` 下的页面。
- 页面职责：展示 Session 控制面和事件流视图，并调用后端 `/api/v1` 接口。
- 当前状态：导航先收敛为 `总览` 与 `会话` 两个模块，页面内容暂为空白占位。
- 目标边界：页面只消费后端契约，不直接复刻数据库或后端内部模型。

### 2. Session 创建

- 入口：`POST /api/v1/sessions`
- 路由：`backend/src/presentation/api/v1/sessions.py`
- 用例：`backend/src/application/usecases/session/create_session.py`
- 存储：`backend/src/infrastructure/persistence/postgres/repositories/session_repository.py`
- 结果：写入 Postgres `sessions` 表，建立 Session 级动作注册表。

### 3. Entity 注册与令牌签发

- 入口：`POST /api/v1/sessions/{session_id}/entities`
- 路由调用 `RegisterEntityUseCase`
- 用例同时协调：
  - Postgres Session 查询
  - Redis 在线态与画像写入
  - HMAC token 签发
- 结果：返回 `entity_id`、`access_token`、`refresh_token`，并激活在线态。

### 4. Event 上报

- 入口：`POST /api/v1/sessions/{session_id}/events`
- 请求先经 `require_session_access_claims` 做 access token 校验。
- `ReportEventUseCase` 执行：
  - 读取 Session，确认 `verb` 已注册。
  - 用 `jsonschema` 校验 `details` 是否符合 `details_schema`。
  - 先写 Mongo Event 载荷，再写 Neo4j Event 骨架。
- 结果：返回 `event_id` 与 accepted 状态。

### 5. Entity Context 读取

- 入口：`GET /api/v1/sessions/{session_id}/entities/{entity_id}/context`
- 鉴权：`require_entity_access_claims`
- `GetEntityContextUseCase` 执行：
  - 确认 Session 存在。
  - 从 Redis 判断 Entity 是否存在或在线。
  - 从 Neo4j 读取近期事件 ID。
  - 从 Mongo 批量补齐详情载荷。
  - 组装 self / incoming / neighbor / global / hot_targets / world_snapshot 六视图。

### 6. Presence 心跳

- 入口：`WS /api/v1/sessions/{session_id}/entities/{entity_id}/presence`
- 鉴权：`require_entity_ws_access_claims`
- 用例：`MaintainEntityPresenceUseCase`
- 行为：
  - 建立连接后写入在线态与心跳 TTL。
  - 断连时清理在线态、心跳和 token 关联状态。

## 横切关注点

- 鉴权
  - access token 保护 Entity 级和 Session 级写接口。
  - refresh token 单次消费；检测到重放时提升 `token_version` 并撤销旧令牌。
  - WebSocket 通过 query 参数传递 `access_token`。
- 校验
  - 请求结构由 Pydantic schema 校验。
  - Event 业务载荷由 `jsonschema` 结合 `Session.actions` 校验。
  - 统一异常经 `backend/src/presentation/api/exception_handlers.py` 转为 API 错误响应。
- 持久化
  - Postgres 是 Session 控制面的真相源。
  - Redis 负责在线态、运行态、展示名唯一索引和鉴权状态。
  - Mongo 保存完整 Event 载荷。
  - Neo4j 保存面向查询的图谱关系骨架。
- 可靠性
  - 启动时检查后端依赖可达性，但不因单点失败直接拒绝启动。
  - Event 写入遵守“先 Mongo、后 Neo4j”的双写顺序。
- 可观测性
  - 启动失败与依赖异常记录到日志。
  - `backend/src/infrastructure/observability/` 是后续统一接入点，但当前能力较轻。
- 工程入口
  - 管理台相关命令从 `apps/admin/` 执行。
  - `uv`、pytest、ruff、Alembic 都应从 `backend/` 作为工作目录执行。
  - 根目录 `.env` 由 `backend/src/core/config.py` 显式加载。

## 相关文件

- `backend/src/main.py`
- `backend/src/presentation/api/dependencies.py`
- `backend/src/application/usecases/event/report_event.py`
- `backend/src/application/usecases/entity/get_entity_context.py`
- `backend/src/domain/session/actions.py`
- `backend/src/infrastructure/persistence/postgres/models.py`
- `backend/alembic.ini`
- `backend/.env.example`
- `apps/admin/package.json`
- `apps/admin/app/page.tsx`
- `docs/design-docs/backend-spec.md`
- `docs/design-docs/api-contract.md`
- `docs/FRONTEND.md`
- `docs/SECURITY.md`
- `docs/RELIABILITY.md`
