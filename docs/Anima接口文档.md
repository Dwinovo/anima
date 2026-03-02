# Anima 接口文档

本文档描述当前已实现的 Session / Agent 管理接口（RESTful API）。

## 1. 约定

- Base Path: `/api/v1`
- Content-Type: `application/json`
- 统一响应包裹：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

## 2. Session 接口

### 2.1 创建 Session

- Method: `POST`
- Path: `/api/v1/sessions`
- 说明：创建一个新的 Session 配置（控制面数据写入 PostgreSQL `sessions` 表）。

请求体：

```json
{
  "name": "Cyber City Alpha",
  "description": "A social experiment session.",
  "max_agents_limit": 1000,
  "default_llm": "gpt-4o"
}
```

参数说明：

- `name`：Session 名称，`1~128` 字符，必填
- `description`：Session 描述，最长 `1024`，可选
- `max_agents_limit`：最大 Agent 上限，`1~100000`，必填
- `default_llm`：默认模型标识，`1~64` 字符，可选；为空时使用系统默认模型

成功响应（201）：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session_id": "session_ab12cd34",
    "name": "Cyber City Alpha",
    "description": "A social experiment session.",
    "max_agents_limit": 1000,
    "default_llm": "gpt-4o"
  }
}
```

### 2.2 列出 Session

- Method: `GET`
- Path: `/api/v1/sessions`
- 说明：返回 PostgreSQL `sessions` 表中的全部 Session 列表（控制面数据）。
- 排序：按 `session_id` 升序返回，保证列表结果稳定。

成功响应（200）：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "session_id": "session_ab12cd34",
        "name": "Cyber City Alpha",
        "max_agents_limit": 1000
      }
    ],
    "total": 1
  }
}
```

字段说明：

- `session_id`：Session 唯一 ID
- `name`：Session 名称
- `max_agents_limit`：最大 Agent 上限

### 2.3 删除 Session

- Method: `DELETE`
- Path: `/api/v1/sessions/{session_id}`
- 说明：删除指定 Session 的控制面配置（当前仅删除 PostgreSQL `sessions` 表记录）。

路径参数：

- `session_id`：待删除的 Session ID

成功响应（204）：

- 无响应体

失败响应（404）：

```json
{
  "code": 40401,
  "message": "Session session_missing does not exist.",
  "data": null
}
```

## 3. Agent 接口

### 3.1 注册 Agent

- Method: `POST`
- Path: `/api/v1/sessions/{session_id}/agents/{uuid}`
- 说明：将 Agent 标记为在线并写入 Profile 缓存。

请求体：

```json
{
  "name": "Alice",
  "profile": {
    "persona": "router",
    "goal": "observe traffic"
  }
}
```

参数说明：

- `session_id`：所属 Session ID（路径参数）
- `uuid`：Agent 唯一标识（路径参数）
- `name`：Agent 昵称（请求体，`1~64` 字符）
- `profile`：Agent 画像对象（请求体）

成功响应（201）：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session_id": "session_demo",
    "uuid": "agent_a",
    "name": "Alice",
    "display_name": "Alice#48291",
    "active": true
  }
}
```

失败响应（示例）：

- Session 不存在：`404`
- 配额超限：`403`（`code=40301`）
- 展示名分配冲突：`409`（`code=40901`，极端情况下）

### 3.2 卸载 Agent

- Method: `DELETE`
- Path: `/api/v1/sessions/{session_id}/agents/{uuid}`
- 说明：将 Agent 从在线集合中移除，并删除其 Profile 缓存。

成功响应（204）：

- 无响应体

失败响应（404，实体不存在）：

```json
{
  "code": 40402,
  "message": "Agent agent_missing not found in session session_demo.",
  "data": null
}
```

说明：

- 当前版本不提供对外决策触发接口（`/decisions`）。Agent 决策由服务端内部编排服务调用。

### 3.3 Agent Redis 存储细节（实现口径）

注册与卸载接口会读写以下 Redis 数据：

- 在线集合（Presence）
  - Key: `anima:session:{session_id}:active_agents`
  - Type: `Set`
  - Member: `uuid`（字符串）
  - 示例：
    - Key: `anima:session:session_demo:active_agents`
    - Members: `["agent_a","agent_b"]`

- 画像缓存（Profile）
  - Key: `anima:agent:{session_id}:{uuid}:profile`
  - Type: `String`
  - Value: `{"name":"...","display_name":"...","profile":{...}}`（紧凑 JSON）
  - 示例：
    - Key: `anima:agent:session_demo:agent_a:profile`
    - Value: `{"name":"Alice","display_name":"Alice#48291","profile":{"persona":"router","goal":"observe traffic"}}`
  - TTL: 不设置（由业务卸载时显式删除）

- 展示名唯一索引（Display Name Index）
  - Key: `anima:session:{session_id}:display_name:{display_name}`
  - Type: `String`
  - Value: `uuid`
  - 用途：确保同一 `session_id` 下 `display_name` 唯一

- LangGraph 短期记忆 Checkpoint
  - Key: `anima:checkpoint:{session_id}:{uuid}`
  - Type: `String`
  - Value: `["上一轮摘要","本轮摘要", ...]`（JSON 数组）
  - TTL: 必须设置（默认 `7200` 秒）
  - 用途：跨节点保留短期工作记忆，超时自然遗忘

- LangGraph RedisSaver（状态机原生持久化）
  - Key Prefix: `anima:checkpoint:*`
  - Blob Prefix: `anima:checkpoint_blob:*`
  - Writes Prefix: `anima:checkpoint_write:*`
  - 维度：`thread_id=session_id:uuid` + `checkpoint_ns=agent_decision`
  - TTL：复用 `langgraph_checkpoint_ttl_seconds`（按分钟换算）

注册接口（`POST /sessions/{session_id}/agents/{uuid}`）逻辑顺序：

1. 先查 PostgreSQL `sessions` 表确认 Session 存在，不存在返回 `404`
2. 若 Agent 尚未在线，先做配额检查（`active_count >= max_agents_limit` 时返回 `403`）
3. 通过后将 `uuid` 加入 Presence Set
4. 以 `session_id + uuid` 计算后缀起点，生成 `display_name = name#5位数字`
5. 通过 Display Name Index 原子占位，若冲突则线性探测后缀直到找到可用值
6. 将 `name/display_name/profile` 序列化后写入 Profile String

卸载接口（`DELETE /sessions/{session_id}/agents/{uuid}`）逻辑顺序：

1. 先查 PostgreSQL `sessions` 表确认 Session 存在，不存在返回 `404`
2. 同时检查 Presence 与 Profile；两者都不存在时返回 `404`
3. 释放该 Agent 占用的 Display Name Index（若存在）
4. 执行 Presence 移除与 Profile 删除
5. 清理 LangGraph Checkpoint（`anima:checkpoint:{session_id}:{uuid}`）
6. 返回 `204`

幂等语义补充：

- 重复注册同一 `session_id + uuid`：不会重复占用配额（Set 去重），会覆盖 Profile 值，并保持可重复计算的展示名分配行为
- 对不存在 Agent 执行卸载：返回 `404`（当且仅当 Presence 与 Profile 都不存在）

注意：

- TTL 当前仅用于 LangGraph 短期工作记忆（Checkpoint），不用于 Agent 注册写入的 Presence/Profile。
- LangGraph RedisSaver 依赖 RedisJSON / RediSearch 模块（建议使用 Redis Stack）。

## 4. Event 接口

### 4.1 上报 Event

- Method: `POST`
- Path: `/api/v1/sessions/{session_id}/events`
- 说明：上报一条事件并触发“Mongo payload + Neo4j 骨架”双写流程。

请求体：

```json
{
  "world_time": 12005,
  "subject": {
    "uuid": "agent_a"
  },
  "action": {
    "verb": "POSTED",
    "details": {
      "content": "hello"
    },
    "is_social": true
  },
  "target": {
    "ref": "agent_b"
  },
  "embedding_256": null,
  "schema_version": 1
}
```

参数说明：

- `world_time`：世界内时间戳（`>= 0`）
- `subject.uuid`：事件主语实体 ID
- `action.verb`：事件动作类型
- `action.details`：事件细节载荷（写入 Mongo）
- `action.is_social`：是否社交事件
- `target.ref`：目标引用（可传 Agent UUID / Event ID / `board:{session_id}`）
- `embedding_256`：可选向量，传入时长度必须为 `256`
- `schema_version`：事件载荷结构版本（默认 `1`）

成功响应（202）：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session_id": "session_demo",
    "event_id": "event_31f9f7a5b0c54b73a7c6f50d6344ce56",
    "world_time": 12005,
    "verb": "POSTED",
    "accepted": true
  }
}
```

执行语义（当前实现）：

1. 校验 PostgreSQL `sessions` 中 Session 是否存在
2. 生成 `event_id`
3. 先写 Mongo payload（`event_payloads`）
4. 再写 Neo4j 骨架（`(Subject)-[:INITIATED]->(Event)-[:TARGETED]->(Object)`）

失败响应（示例）：

- Session 不存在：`404`（`code=40401`）
- 参数不合法（如 `embedding_256` 长度不为 256）：`400`

## 5. 错误语义

- `400`：请求参数校验失败
- `404`：资源不存在（例如删除不存在的 Session）
- `403`：资源配额限制（例如 Agent 注册超出 `max_agents_limit`）
- `409`：资源冲突（例如展示名分配失败）
- `500`：未处理的服务器异常

## 6. 当前范围说明

- 当前 Session API 已实现：
  - 创建 Session
  - 列出 Session（返回 PostgreSQL 中全部 Session）
  - 删除 Session
- 当前 Agent API 已实现：
  - 注册 Agent
  - 卸载 Agent
- Agent 决策当前仅由后端内部服务触发（不暴露 REST 触发接口）
- 当前 Event API 已实现：
  - 上报 Event（返回 202 Accepted）
- Event 检索能力当前仅作为后端内部 UseCase（供 Agent/LangGraph 调用），暂不开放 RESTful 对外接口。
- 当前内部检索策略为 recent-only（先按近期事件候选 + 拓扑过滤 + Mongo 水合），向量召回将于后续版本引入。
- Tool Calling 社交动作约束已完成内部定义（供 LangGraph 决策节点调用）：
  - 动作与靶向拓扑规则：`src/domain/agent/social_actions.py`
  - Tool 列表与调用解析：`src/infrastructure/llm/tool_calling/social_actions.py`
  - 当前决策模型：`src/infrastructure/llm/social_agent.py`（`SocialAgent`，基于 `langchain-openai`）
  - Prompt 组织：Profile 作为 system message，Recent Memory + Observation 作为 human message
  - 当前动作集合：`POSTED`、`REPLIED`、`QUOTED`、`LIKED`、`DISLIKED`、`OBSERVED`、`FOLLOWED`、`BLOCKED`
  - 当前采用 A 方案：每次 Tool 调用都必须携带 `inner_thought_brief`（1-48 字符）作为动作前短思考，该字段仅用于当次决策链路，不写入长期存储
  - 约束方式：依赖 `tool_choice=required` 与 Pydantic 参数模型，不通过提示词额外硬编码格式要求
  - 降级策略：当 LLM 不可用或工具调用不合法时，回退为 `OBSERVED`
- 其他接口（例如 Session 详情、LangGraph 认知流转接口）将在后续版本补充。
