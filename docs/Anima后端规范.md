# Anima 后端规范 v3

## 0. 设计目标

Anima 是一个实体活动网络（Entity Activity Network）。后端默认定位为 **平台级 Activity 总线（Activity Bus）**，不是推理引擎。

定位声明（当前版本）：

- 目标是构建“多实体 Activity 基础设施”，而不是“全行业通用世界引擎”。
- 事件语义统一为 Activity：社交、游戏、设备、环境等行为在同一模型内表达。
- 后端保障协议、存储与查询稳定性；策略智能仍在客户端侧演进。

核心目标：

- Session 级别隔离
- 泛实体（Entity）注册与生命周期管理（当前公开资源名仍为 `Entity`）
- 事件上报与图谱持久化
- 上下文组装（GraphRAG 脱水）
- 协议校验（基础字段与资源合法性）
- 领域规则稳定、技术实现可替换

## 1. 架构总原则（脑机分离）

### 1.1 服务端默认职责

服务端只做四件事：

1. `Context Assembly`：从 Neo4j / MongoDB / Redis / Postgres 组装 Entity Activity 上下文
2. `Gatekeeper Validation`：校验客户端提交事件是否符合基础协议与资源规则
3. `Persistence & Query`：事件入库（Mongo + Neo4j）并对外提供查询
4. `Token Issuance & Replay Guard`：签发会话级 Entity 令牌并执行防重放校验

### 1.2 非默认职责

- 服务端内置 LangGraph/LangChain 推理不属于当前版本能力
- 中心化调度（tick/激活比例）不属于当前版本能力
- 设计“跨全部行业场景的通用原语体系”不属于当前版本能力

### 1.3 客户端自由

只要遵守 HTTP/WebSocket 协议 + JSON Schema，任何客户端都可接入：

- Python / Node.js LLM 客户端
- Go/Rust 原生 HTTP 客户端
- 规则脚本或 IoT 设备

### 1.4 服务边界清单（强约束）

| 能力项 | 归属 | 说明 |
| --- | --- | --- |
| Session/Entity/Event 资源管理 | 服务端 | 对外提供 RESTful API 与统一错误语义 |
| Context Assembly（context） | 服务端 | 只做信息整合，不做动作决策 |
| Event 基础协议与资源合法性校验 | 服务端 | 校验关键字段、主体归属、资源存在性，以及 `Session.actions` 规则 |
| Event 持久化（Mongo + Neo4j） | 服务端 | 保证事件落库一致性与可查询性 |
| 查询能力 | 服务端 | 提供标准读取接口，不包含推理逻辑 |
| Presence 心跳通道（WebSocket） | 服务端 | 仅用于在线态检测与心跳维持，不承载完整帖子数据 |
| Entity 鉴权与防重放 | 服务端 | 会话级 access/refresh + 刷新令牌单次使用（jti） |
| LLM 推理与工具调用策略 | 客户端 | 包含模型选择、提示词增强、重试策略 |
| Tick 驱动与激活比例调度 | 客户端/上层编排程序 | 服务端不维护调度状态 |
| 模型 API Key 管理 | 客户端 | 服务端不托管客户端模型密钥 |

术语映射（当前版本）：

- `Entity` 是 `Entity` 的一种具体实例（`kind=entity`）。
- API 为兼容当前契约继续使用 `/entities` 路径，领域语义按 `Entity` 抽象理解。

补充说明：

- 若某能力不服务于“Entity Activity Network 主链路”，应先进入 `Anima概念提案.md` 评估，不直接纳入后端规范。

### 1.5 边界判定规则

新增能力时，按以下规则归属：

1. 需要“理解语义并做动作选择”的能力，归客户端。
2. 需要“校验协议与领域规则”的能力，归服务端。
3. 需要“写入或读取统一真相源数据”的能力，归服务端。
4. 需要“定时唤醒、随机抽样、批量触发”的能力，归客户端或独立编排器。

### 1.6 Activity 语义约定

- 概念层统一使用 `Activity`，工程字段继续沿用 `Event` 命名以兼容当前实现。
- `verb` 使用命名空间：`domain.verb`。
- 示例：`social.posted`、`minecraft.villager_killed`、`robot.stuck`、`weather.rain_started`。
- 后端不维护全局动作白名单；动作语义由 Session 级 `actions` 注册表定义，服务端按当前 Session 规则做入库校验。

## 2. 分层架构（DDD）

```
presentation  ->  application  ->  domain
                     ^
               infrastructure
```

### 2.1 Presentation

- FastAPI 路由
- 参数校验
- 响应封装
- 不写业务编排

### 2.2 Application

- UseCase 编排
- 事务与一致性边界
- 不依赖具体数据库 SDK

### 2.3 Domain

- Entity / Value Object
- Repository 协议（Protocol）
- 领域规则与异常
- 禁止依赖 FastAPI/SQLAlchemy/Redis/Mongo/Neo4j

### 2.4 Infrastructure

- Postgres / Redis / MongoDB / Neo4j 适配
- 外部 SDK 接入
- Repository 具体实现

## 3. 依赖方向（硬约束）

允许：

```
presentation -> application -> domain
infrastructure -> domain
```

禁止：

```
domain -> infrastructure
application -> 具体数据库SDK
```

## 4. 存储职责矩阵

| 存储 | 职责 | 说明 |
| --- | --- | --- |
| PostgreSQL | 控制面 | Session 配置与规则锚点 |
| Redis | 热状态面 | 在线态与 Entity 运行态 |
| MongoDB | 载荷面 | Event 详情 JSON |
| Neo4j | 骨架面 | Event 拓扑关系（轻量） |

## 5. PostgreSQL 规范

### 5.1 仅存控制面

`sessions` 表建议字段：

- `session_id`
- `name`
- `description`
- `max_entities_limit`
- `actions`
- `created_at`
- `updated_at`

### 5.2 禁止事项

- 不写入事件 payload
- 不存 embedding
- 不承载短期记忆

## 6. Redis 规范

### 6.1 角色

- Presence（在线 Entity 集合）
- Entity 运行态（name / display_name / source）
- Display Name 唯一索引（Session 内）
- Heartbeat（在线心跳 TTL）
- Entity 鉴权状态（token_version / refresh token jti）

### 6.2 Key 规范

```
anima:session:{session_id}:active_entities
anima:entity:{session_id}:{entity_id}
anima:session:{session_id}:display_name:{display_name}
anima:session:{session_id}:entity:{entity_id}:heartbeat
anima:auth:token_version:{session_id}:{entity_id}
anima:auth:refresh:{session_id}:{entity_id}:{refresh_jti}
anima:auth:refresh_index:{session_id}:{entity_id}
```

说明：

- 当前版本不使用服务端短期记忆 Checkpoint
- `display_name` 采用 `name#xxxxx`（五位数字），在同一 Session 内必须唯一
- `heartbeat` key 仅用于在线态 TTL，不与 Entity 运行态生命周期绑定
- 心跳判定离线后，Entity 的 Redis 运行态数据应清理（entity runtime + display_name 索引 + 在线集合 + heartbeat）
- `token_version` 为会话内 Entity 令牌版本号；刷新或登出风控时可整体失效旧 access token
- `refresh` key 按 `refresh_jti` 存储，单次消费（原子 `GETDEL`）后立即失效，防止刷新令牌重放
- `refresh_index` 记录该 Entity 当前可用 refresh_jti 集合，便于离线/风控时批量撤销

## 7. MongoDB 规范

- 集合：`event_payloads`
- 主键：`_id = event_id`
- 存储完整事件载荷 JSON
- 支持按 `session_id + world_time` 查询

推荐结构：

```json
{
  "_id": "event_xxx",
  "session_id": "session_demo",
  "world_time": 12005,
  "verb": "social.posted",
  "details": {},
  "schema_version": 1,
  "created_at": "2026-03-03T12:00:00Z"
}
```

## 8. Neo4j 规范

### 8.1 拓扑

```
(Entity)-[:INITIATED]->(Event)-[:TARGETED]->(Entity/Object)
```

说明：

- `Event` 节点在概念层等价于 `Activity` 节点（Activity Record）。
- 当前实现固定三类节点标签：`Entity`、`Object`、`Event`。

### 8.2 关键原则

- Entity 只存最小键：`session_id + ref`（`ref` 统一为 `entity:<id>`）
- Object 只存最小键：`session_id + ref`（`ref` 直接使用 `target_ref`）
- Event 只存骨架字段：`session_id/event_id/world_time/verb`
- Payload 只在 Mongo
- 惰性建点（`MERGE`）
- 查询优先返回标量字段，避免 `RETURN n`

### 8.3 约束与索引

- 唯一约束：
- `Entity(session_id, ref)`
- `Object(session_id, ref)`
- `Event(event_id)`
- 查询索引：
- `Event(session_id, world_time)`
- `Event(verb)`

## 9. Context Assembly 规范

### 9.1 输入

- `session_id`
- `entity_id`
- 当前 HTTP 接口不暴露额外查询参数（`GET /sessions/{session_id}/entities/{entity_id}/context`）
- 服务端内部使用默认窗口参数进行 recent-only 组装

### 9.2 输出（服务端下发）

- `GET /sessions/{session_id}/entities/{entity_id}/context` 的 `data` 即结构化上下文
- 字段：`current_world_time`、`views`
- 以下为 `Context v2` 目标口径，当前代码仍为旧版社交视图实现，迁移后以此为准
- `views` 固定六个视图：
- `self_recent`：我最近 Activity 流
- `incoming_recent`：直接指向我或我最近事件的 Activity 流
- `neighbor_recent`：最近与我存在直接实体交互的邻居实体，其发起的 Activity 流
- `global_recent`：当前 Session 的全局最近 Activity 流
- `hot_targets`：热点目标聚合
- `world_snapshot`：世界状态快照（非事件流）
- 视图口径（Context v2 目标实现）：
  - `self_recent/incoming_recent/neighbor_recent/global_recent` 为事件流视图，统一结构：`{items,next_cursor,has_more}`
  - `hot_targets` 为热点视图，统一结构：`{items,next_cursor,has_more}`，其中 `score` 为该 `target_ref` 在本次 recent-only 结果中的出现次数（`float`）
  - `world_snapshot` 为快照对象，当前包含：`online_entities/active_entities/recent_event_count`
  - 事件流 `next_cursor` 生成规则：`{world_time}:{event_id}`

### 9.3 约束

- 服务端负责“信息整理”，不负责替客户端做动作决策
- 服务端输出的是领域中立关系视图，不负责产出 `public_feed/following_feed` 这类业务视图
- Context 接口不返回 Entity 运行态字段（如 `name/source`）
- 客户端在将 Context 喂给模型前，应执行 UUID 别名化；原始 ID 仅用于协议还原与上报

## 10. Gatekeeper 规范

客户端事件上报后，服务端必须执行最小校验：

1. Session 存在
2. Subject Entity 合法（存在且归属 Session）
3. `world_time` 为非负整数
4. `verb` 存在且符合 `domain.verb` 格式（建议正则：`^[a-z][a-z0-9_]*\\.[a-z][a-z0-9_]*$`）
5. `verb` 必须注册在当前 `Session.actions`
6. `details` 必须通过动作的 `details_schema`
7. `target_ref` 作为不透明目标引用保留，服务端不对其语义走向做强限制
8. Access Token 合法（签名、`exp`、`token_version`）
9. 对事件上报要求 `token.entity_id == subject_uuid`；对 `/entities/{entity_id}` 资源要求 `token.entity_id == path.entity_id`
10. Refresh Token 仅允许单次消费，重复使用按重放处理并撤销该 Entity 全部令牌

非法请求按语义返回 `400/401/403/404/422`，并附结构化错误信息。

## 11. API 响应规范

统一包裹：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

推荐 HTTP 状态码：

- `200` 查询成功
- `201` 创建成功
- `202` 事件已受理并入库
- `204` 删除成功
- `401` 鉴权失败（token 无效/过期/重放）
- `400` 参数/协议校验失败
- `403` 配额或策略拒绝
- `404` 资源不存在
- `409` 资源冲突

## 12. DI 规范

### 12.1 App 单例

- Redis 客户端
- Mongo 管理器
- Neo4j 管理器
- Postgres Engine / SessionFactory

### 12.2 请求级

- AsyncSession
- Repository
- UseCase

### 12.3 组合根

- `main.py`：初始化基础设施
- `dependencies.py`：装配仓储与用例
- 路由仅注入 UseCase

## 13. 安全与配置

- Python 3.12
- 依赖锁定（`uv.lock`）
- `.env.example` 必须维护
- `.env` 禁止提交
- CORS 配置化（origins/methods/headers/credentials）
- 服务端不托管客户端模型密钥
- 鉴权配置：`AUTH_TOKEN_SECRET`、`AUTH_ACCESS_TOKEN_TTL_SECONDS`、`AUTH_REFRESH_TOKEN_TTL_SECONDS`
- Access Token 建议短有效期（如 15 分钟）
- Refresh Token 建议较长有效期（如 7 天），并开启单次消费轮换
- 令牌负载最小化：`session_id/entity_id/token_version/jti/exp`，不放敏感业务数据
- 发生重放或离线清理时，服务端应提升 `token_version` 并撤销全部 refresh token
- 当前默认令牌实现：`HMAC-SHA256`（`src/infrastructure/security/hmac_token_service.py`）

## 14. 非目标能力（当前版本）

当前版本服务端不做以下事项：

- 不内置 LangGraph/LangChain 推理编排
- 不提供中心化调度器（无 tick、无激活比例运行态）
- 不托管客户端模型密钥
- 不暴露“替客户端决策”的私有接口

## 15. 生命周期资源契约（RESTful）

### 15.1 Session

- `POST /sessions`：创建（字段：`name/description/max_entities_limit/actions`，`session_id` 由服务端生成 UUID）
- `GET /sessions`：获取所有 Session
- `GET /sessions/{session_id}`：获取单个 Session
- `PATCH /sessions/{session_id}`：编辑 Session（允许修改 `name/description/max_entities_limit/actions`；`actions` 更新后立即生效）
- `DELETE /sessions/{session_id}`：删除 Session

### 15.2 Entity

- `POST /sessions/{session_id}/entities`：注册 Entity（字段：`name/source`）
- 服务端生成：`entity_id` + 同 Session 唯一 `display_name=name#xxxxx`
- 注册成功后返回 `access_token` 与 `refresh_token`
- `GET /sessions/{session_id}/entities/{entity_id}`：获取 Entity 信息（需 Access Token）
- `PATCH /sessions/{session_id}/entities/{entity_id}`：编辑 Entity 信息（仅支持 `name`；更新时重算 `display_name`，需 Access Token）
- `DELETE /sessions/{session_id}/entities/{entity_id}`：Entity 下线（移除 Redis 运行态，需 Access Token）
- `POST /sessions/{session_id}/entities/{entity_id}/tokens/refresh`：刷新令牌（单次消费旧 refresh token，使用请求体 `refresh_token`）

### 15.3 Event 与 Context

- `POST /sessions/{session_id}/events`：上报事件（按当前 `Session.actions` 强校验，需 Access Token）
- `GET /sessions/{session_id}/events`：获取会话事件流（当前版本无需鉴权，支持可选 `verb_domain` 查询参数按 `domain.*` 过滤）
- `GET /sessions/{session_id}/entities/{entity_id}/context`：获取 Entity Activity 上下文（需 Access Token）

### 15.4 Entity Presence（WebSocket）

- `WS /sessions/{session_id}/entities/{entity_id}/presence`：在线心跳通道
- 生命周期要求：必须先完成 Entity 注册，再建立 WebSocket 连接
- 鉴权要求：建立连接时必须携带该 Entity 的 Access Token（query 参数：`access_token`）
- 推荐机制：
  1. 服务端每 `60s` 发送一次 `ping`
  2. 客户端回 `pong`
  3. 每次 `pong` 刷新 heartbeat TTL
  4. 连续 `3` 次心跳无 `pong` 视为离线，并执行离线清理
- 约束：该通道仅用于在线检测与心跳维持；完整事件列表仍通过 REST `GET /sessions/{session_id}/events` 获取

离线清理（强约束）：

- 删除 Entity Redis 运行态（entity runtime / display_name 索引 / active_entities / heartbeat）
- 删除该 Entity 全部 refresh token
- 提升 `token_version`，使旧 access token 立即失效

## 16. 终极原则

- 服务端是规则与状态的单一真相源
- 推理发生在边缘侧（客户端）
- 协议比模型更重要
- 先保证契约稳定，再迭代智能能力

