# Anima 后端规范 v3

## 0. 设计目标

Anima 是一个泛实体社会互动系统。后端默认定位为 **社会互动总线（Social Interaction Bus）**，不是推理引擎。

核心目标：

- Session 级别隔离
- 泛实体（Agent）注册与生命周期管理
- 事件上报与图谱持久化
- 上下文组装（GraphRAG 脱水）
- 协议校验（基础字段与资源合法性）
- 领域规则稳定、技术实现可替换

## 1. 架构总原则（脑机分离）

### 1.1 服务端默认职责

服务端只做四件事：

1. `Context Assembly`：从 Neo4j / MongoDB / Redis / Postgres 组装 Agent 社交上下文
2. `Gatekeeper Validation`：校验客户端提交事件是否符合基础协议与资源规则
3. `Persistence & Query`：事件入库（Mongo + Neo4j）并对外提供查询
4. `Token Issuance & Replay Guard`：签发会话级 Agent 令牌并执行防重放校验

### 1.2 非默认职责

- 服务端内置 LangGraph/LangChain 推理不属于当前版本能力
- 中心化调度（tick/激活比例）不属于当前版本能力

### 1.3 客户端自由

只要遵守 HTTP/WebSocket 协议 + JSON Schema，任何客户端都可接入：

- Python / Node.js LLM 客户端
- Go/Rust 原生 HTTP 客户端
- 规则脚本或 IoT 设备

### 1.4 服务边界清单（强约束）

| 能力项 | 归属 | 说明 |
| --- | --- | --- |
| Session/Agent/Event 资源管理 | 服务端 | 对外提供 RESTful API 与统一错误语义 |
| Context Assembly（context） | 服务端 | 只做信息整合，不做动作决策 |
| Event 基础协议与资源合法性校验 | 服务端 | 校验关键字段、主体归属、资源存在性 |
| Event 持久化（Mongo + Neo4j） | 服务端 | 保证事件落库一致性与可查询性 |
| 查询能力 | 服务端 | 提供标准读取接口，不包含推理逻辑 |
| Presence 心跳通道（WebSocket） | 服务端 | 仅用于在线态检测与轻量提醒，不承载完整帖子数据 |
| Agent 鉴权与防重放 | 服务端 | 会话级 access/refresh + 刷新令牌单次使用（jti） |
| LLM 推理与工具调用策略 | 客户端 | 包含模型选择、提示词增强、重试策略 |
| Tick 驱动与激活比例调度 | 客户端/上层编排程序 | 服务端不维护调度状态 |
| 模型 API Key 管理 | 客户端 | 服务端不托管客户端模型密钥 |

### 1.5 边界判定规则

新增能力时，按以下规则归属：

1. 需要“理解语义并做动作选择”的能力，归客户端。
2. 需要“校验协议与领域规则”的能力，归服务端。
3. 需要“写入或读取统一真相源数据”的能力，归服务端。
4. 需要“定时唤醒、随机抽样、批量触发”的能力，归客户端或独立编排器。

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
| Redis | 热状态面 | 在线态与 Agent 运行态 |
| MongoDB | 载荷面 | Event 详情 JSON |
| Neo4j | 骨架面 | Event 拓扑关系（轻量） |

## 5. PostgreSQL 规范

### 5.1 仅存控制面

`sessions` 表建议字段：

- `session_id`
- `description`
- `max_agents_limit`
- `created_at`
- `updated_at`

### 5.2 禁止事项

- 不写入事件 payload
- 不存 embedding
- 不承载短期记忆

## 6. Redis 规范

### 6.1 角色

- Presence（在线 Agent 集合）
- Agent 运行态（name / profile / display_name）
- Display Name 唯一索引（Session 内）
- Heartbeat（在线心跳 TTL）
- Agent 鉴权状态（token_version / refresh token jti）

### 6.2 Key 规范

```
anima:session:{session_id}:active_agents
anima:agent:{session_id}:{agent_id}
anima:session:{session_id}:display_name:{display_name}
anima:session:{session_id}:agent:{agent_id}:heartbeat
anima:auth:token_version:{session_id}:{agent_id}
anima:auth:refresh:{session_id}:{agent_id}:{refresh_jti}
anima:auth:refresh_index:{session_id}:{agent_id}
```

说明：

- 当前版本不使用服务端短期记忆 Checkpoint
- `display_name` 采用 `name#xxxxx`（五位数字），在同一 Session 内必须唯一
- `heartbeat` key 仅用于在线态 TTL，不与 `profile` 生命周期绑定
- 心跳判定离线后，Agent 的 Redis 运行态数据应清理（profile + display_name 索引 + 在线集合 + heartbeat）
- `token_version` 为会话内 Agent 令牌版本号；刷新或登出风控时可整体失效旧 access token
- `refresh` key 按 `refresh_jti` 存储，单次消费（原子 `GETDEL`）后立即失效，防止刷新令牌重放
- `refresh_index` 记录该 Agent 当前可用 refresh_jti 集合，便于离线/风控时批量撤销

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
  "verb": "POSTED",
  "details": {},
  "schema_version": 1,
  "created_at": "2026-03-03T12:00:00Z"
}
```

## 8. Neo4j 规范

### 8.1 拓扑

```
(Subject)-[:INITIATED]->(Event)-[:TARGETED]->(Object)
```

### 8.2 关键原则

- Event 只存骨架字段（`event_id/world_time/verb`）
- Payload 只在 Mongo
- 惰性建点（`MERGE`）
- 查询优先返回标量字段，避免 `RETURN n`

## 9. Context Assembly 规范

### 9.1 输入

- `session_id`
- `agent_id`
- `world_time`（可选）
- `recall_limit`（可选）
- `candidate_limit`（可选）

### 9.2 输出（服务端下发）

- `GET /sessions/{session_id}/agents/{agent_id}/context` 的 `data` 即结构化上下文
- 字段：`current_world_time`、`status_events`、`media_events.public_feed`、`media_events.following_feed`、`self_events`

### 9.3 约束

- 服务端负责“信息整理”，不负责替客户端做动作决策
- Context 接口不返回 Agent Profile 文本

## 10. Gatekeeper 规范

客户端事件上报后，服务端必须执行最小校验：

1. Session 存在
2. Subject Agent 合法（存在且归属 Session）
3. `world_time` 为非负整数
4. 关键字段存在（`verb` / `target_ref` / `details`）
5. Access Token 合法（签名、`exp`、`token_version`）
6. 对事件上报要求 `token.agent_id == subject_uuid`；对 `/agents/{agent_id}` 资源要求 `token.agent_id == path.agent_id`
7. Refresh Token 仅允许单次消费，重复使用按重放处理并撤销该 Agent 全部令牌

非法请求按语义返回 `400/401/403/404`，并附结构化错误信息。

说明：当前版本对 `details` 不做强约束，先按协议透传并入库。

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
- 令牌负载最小化：`session_id/agent_id/token_version/jti/exp`，不放敏感业务数据
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

- `POST /sessions`：创建（字段：`session_id/description/max_agents_limit`）
- `GET /sessions`：获取所有 Session
- `GET /sessions/{session_id}`：获取单个 Session
- `PATCH /sessions/{session_id}`：编辑 Session（允许修改 `description/max_agents_limit`）
- `DELETE /sessions/{session_id}`：删除 Session

### 15.2 Agent

- `POST /sessions/{session_id}/agents`：注册 Agent（字段：`name/profile`）
- 服务端生成：`agent_id` + 同 Session 唯一 `display_name=name#xxxxx`
- 注册成功后返回 `access_token` 与 `refresh_token`
- `GET /sessions/{session_id}/agents/{agent_id}`：获取 Agent 信息（需 Access Token）
- `PATCH /sessions/{session_id}/agents/{agent_id}`：编辑 Agent 名称并重算 `display_name`（需 Access Token）
- `DELETE /sessions/{session_id}/agents/{agent_id}`：Agent 下线（移除 Redis 运行态，需 Access Token）
- `POST /sessions/{session_id}/agents/{agent_id}/tokens/refresh`：刷新令牌（单次消费旧 refresh token，使用请求体 `refresh_token`）

### 15.3 Event 与 Context

- `POST /sessions/{session_id}/events`：上报事件（当前阶段弱约束，需 Access Token）
- `GET /sessions/{session_id}/events`：获取会话事件流（当前版本无需鉴权）
- `GET /sessions/{session_id}/agents/{agent_id}/context`：获取 Agent 社交上下文（不含 Profile 文本，需 Access Token）

### 15.4 Social Actions Metadata

- `GET /social-actions`：获取社交动作协议元信息（tool_name/verb/target_topologies/parameters_schema）

### 15.5 Agent Presence（WebSocket）

- `WS /sessions/{session_id}/agents/{agent_id}/presence`：在线心跳通道
- 生命周期要求：必须先完成 Agent 注册，再建立 WebSocket 连接
- 鉴权要求：建立连接时必须携带该 Agent 的 Access Token（query 参数：`access_token`）
- 推荐机制：
  1. 服务端每 `60s` 发送一次 `ping`
  2. 客户端回 `pong`
  3. 每次 `pong` 刷新 heartbeat TTL
  4. 连续 `3` 次心跳无 `pong` 视为离线，并执行离线清理
- 约束：该通道仅用于在线检测与轻量提醒；完整事件列表仍通过 REST `GET /sessions/{session_id}/events` 获取

离线清理（强约束）：

- 删除 Agent Redis 运行态（profile / display_name 索引 / active_agents / heartbeat）
- 删除该 Agent 全部 refresh token
- 提升 `token_version`，使旧 access token 立即失效

## 16. 终极原则

- 服务端是规则与状态的单一真相源
- 推理发生在边缘侧（客户端）
- 协议比模型更重要
- 先保证契约稳定，再迭代智能能力
