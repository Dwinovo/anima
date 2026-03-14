# Session Actions Contract Design

## Goal

将 `Session` 从“纯控制面元数据”扩展为“带动作约束的世界规则包”：

- `POST /api/v1/sessions` 创建时必须提交 `actions`
- `PATCH /api/v1/sessions/{session_id}` 允许更新 `actions`
- 规则修改后立即生效
- `POST /api/v1/sessions/{session_id}/events` 必须按当前最新 `session.actions` 做强校验
- 历史事件不回写、不重算、不补校验

## Why

现在服务端仍然把动作约束留在客户端本地目录里，这会导致同一 `Session` 下不同客户端可能持有不一致的动作集：

- 有的客户端允许 `social.replied`
- 有的客户端允许 `combat.attacked`
- 有的客户端对 `details` 结构要求完全不同

这和 `Session` 作为世界规则锚点的定位冲突。既然服务端负责图谱关系整合和入库 gatekeeping，那么它也必须负责“这个世界允许哪些动作”。

## Scope

本次改动只解决三件事：

1. `Session` 存储并返回 `actions`
2. `Session` 创建/更新时校验 `actions` 结构
3. `Event` 上报时基于当前 `session.actions` 做强校验

本次不做：

- 独立的 `/action-registry` 资源
- 动作版本历史
- 历史 event 追溯到旧规则版本
- 客户端 tool 自动生成

## Action Registry Shape

`actions` 采用内联结构，直接挂在 `Session` 上：

```json
[
  {
    "verb": "social.posted",
    "description": "发布内容到公共板",
    "allowed_target_topologies": ["board"],
    "details_schema": {
      "type": "object",
      "required": ["content"],
      "properties": {
        "content": {"type": "string", "minLength": 1}
      },
      "additionalProperties": false
    }
  },
  {
    "verb": "combat.attacked",
    "description": "攻击某个实体",
    "allowed_target_topologies": ["entity"],
    "details_schema": {
      "type": "object",
      "required": ["damage"],
      "properties": {
        "damage": {"type": "integer", "minimum": 1}
      },
      "additionalProperties": false
    }
  }
]
```

## Topology Model

服务端不理解“帖子”“战斗日志”这类业务名词，但需要理解目标引用的基本拓扑类型，用于强校验。

本次支持 4 种目标拓扑：

1. `board`
   - `target_ref` 形如 `board:{session_id}`

2. `event`
   - `target_ref` 形如 `event_xxx`

3. `entity`
   - `target_ref` 形如 `entity:{id}`
   - 或当前兼容形态的裸 Entity ID（无冒号）

4. `object`
   - 其他带前缀但不属于 `board/entity/event` 的引用
   - 例如 `location:forest_gate`、`item:sword_1`

这个划分保持领域中立：社交、战斗、观察、物品交互都能复用。

## Validation Rules

### Session create / patch

- `actions` 为动作定义数组
- 创建时必须提供，且不能为空
- PATCH 时可选；如果提供，也不能为空
- `verb` 必须满足 `domain.verb`
- `verb` 在同一 Session 内必须唯一
- `allowed_target_topologies` 必须非空，成员必须来自固定枚举
- `details_schema` 必须是 JSON object schema，至少要求 `type=object`

### Event report

服务端在写 Mongo/Neo4j 之前执行规则校验：

1. `verb` 必须存在于当前 `session.actions`
2. `target_ref` 解析出的 topology 必须在该动作允许列表中
3. `details` 必须通过该动作的 `details_schema` 校验

若任一步失败，则拒绝入库。

## Storage Strategy

`sessions` 表新增 `actions` JSON 列。

设计取舍：

- 不拆分成 `session_actions` 子表
- 不单独引入 registry 资源
- 直接把当前规则快照挂在 Session 上

原因：

- 当前需求是“创建 Session 时必须提交动作注册”
- `actions` 总是和 `Session` 同步读写
- 先用 JSON 能最快落地，后续若需要审计/复用再拆表

## Runtime Semantics

- `POST /sessions` 写入完整 `actions`
- `PATCH /sessions/{session_id}` 更新 `actions` 后立即生效
- `POST /events` 永远读取当前最新 `session.actions`
- 老事件保持原样，不做二次解释

这意味着服务端只对“写入时是否合法”负责，不对“历史事件当时依据哪版规则通过”负责。

## API Contract Changes

需要同步更新的资源契约：

- `SessionCreateRequest` 新增必填 `actions`
- `SessionPatchRequest` 新增可选 `actions`
- `SessionCreateData` / `SessionDetailData` 返回 `actions`
- `GET /sessions/{session_id}` 返回当前动作约束

`GET /sessions` 仍可保持轻量列表，不必返回完整 `actions`。

## Error Handling

新增事件规则校验异常：

- `verb` 未注册
- `target_ref` 拓扑不匹配
- `details` 不符合 schema

建议统一走业务异常通道，返回 `422`，并在 `details` 中带上失败原因、`verb`、`target_ref` 或 schema 错误摘要。

## Testing Strategy

至少覆盖：

1. Session 请求 schema：
   - 创建必须带 `actions`
   - PATCH 可更新 `actions`
   - 重复 `verb` 被拒绝

2. Session usecase：
   - 创建后能保留 `actions`
   - PATCH 后能更新 `actions`

3. Event usecase：
   - 未注册 `verb` 拒绝
   - 错误 topology 拒绝
   - `details` schema 不匹配拒绝
   - 合法事件仍保持 Mongo -> Neo4j 双写顺序

4. Persistence：
   - `SessionModel` / repository 正确存取 `actions`
   - Alembic 迁移新增 `actions` 列
