# Anima 管理面板设计文档

本文档定义 Anima 管理面板（Next.js）V1。当前管理面板只负责 Session 控制面管理与事件流查看。

## 1. 产品范围

### 1.1 V1 必做

- 创建 Session
- 查询 Session 列表
- 查看单个 Session
- 编辑 Session
- 删除 Session
- 查看 Session 事件流

### 1.2 V1 不做

- Agent 注册/改名/下线（由客户端完成）
- 推理调度、模型管理
- 向量检索与图谱可视化编辑

## 2. 依赖后端接口

### 2.1 Session

- `POST /api/v1/sessions`
- `GET /api/v1/sessions`
- `GET /api/v1/sessions/{session_id}`
- `PATCH /api/v1/sessions/{session_id}`
- `DELETE /api/v1/sessions/{session_id}`

### 2.2 Event

- `GET /api/v1/sessions/{session_id}/events`

## 3. Session 字段口径

管理面板只使用以下字段：

- `session_id`（创建时必填，字符串 UUID/业务 ID）
- `description`（后端可选，管理面板可按产品策略要求必填）
- `max_agents_limit`（创建时必填，正整数）

说明：

- 不再使用 `name`
- 不再使用 `default_llm`
- `session_id` 创建后不可编辑

## 4. 页面设计

## 4.1 `/sessions` 会话管理页

功能：

- Session 列表展示
- 创建 Session
- 编辑 Session
- 删除 Session

列表列：

- `session_id`
- `description`
- `max_agents_limit`
- 操作（查看、编辑、删除）

创建弹窗字段：

- `session_id`
- `description`
- `max_agents_limit`

编辑弹窗字段：

- `description`
- `max_agents_limit`

## 4.2 `/sessions/[sessionId]` 会话详情页

顶部信息：

- `session_id`
- `description`
- `max_agents_limit`

主体：

- 事件流时间线（按 `world_time DESC, event_id DESC`）
- 支持“加载更多”

## 5. 交互流程

### 5.1 创建 Session

1. 打开创建弹窗
2. 填写 `session_id/description/max_agents_limit`
3. 调用 `POST /api/v1/sessions`
4. 成功后刷新列表并提示成功

### 5.2 编辑 Session

1. 进入编辑弹窗
2. 修改 `description/max_agents_limit`
3. 调用 `PATCH /api/v1/sessions/{session_id}`
4. 成功后刷新列表与详情数据

### 5.3 删除 Session

1. 二次确认
2. 调用 `DELETE /api/v1/sessions/{session_id}`
3. 成功后刷新列表

## 6. 前端类型建议（TypeScript）

```ts
export type ApiResponse<T> = {
  code: number
  message: string
  data: T
}

export type SessionListItem = {
  session_id: string
  description: string
  max_agents_limit: number
}

export type SessionDetailData = {
  session_id: string
  description: string
  max_agents_limit: number
  created_at: string
  updated_at: string
}

export type SessionCreatePayload = {
  session_id: string
  description: string
  max_agents_limit: number
}

export type SessionPatchPayload = Partial<{
  description: string
  max_agents_limit: number
}>

export type SessionEventItem = {
  event_id: string
  world_time: number
  verb: string
  subject_uuid: string
  target_ref: string
  details: Record<string, unknown>
  schema_version: number
  is_social: boolean
}
```

## 7. 错误处理

- `400`：字段校验失败（弹窗内展示字段错误）
- `404`：资源不存在（列表刷新或跳转空态）
- `409`：冲突（例如 `session_id` 已存在）
- `500`：通用错误提示 + 重试
