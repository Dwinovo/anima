# Session Target Constraints Design

## Goal

将 Session 动作约束从单层的目标类型白名单，升级为：

- `target_types`
- `target_constraints`

并废弃当前的 `allowed_target_topologies` 命名。

这次改动的目的不是继续为每种目标类型补专用字段，而是给目标约束建立统一扩展位，使服务端可以在入库前校验：

- 目标是什么类型
- 目标还满足哪些更细粒度的条件

## Why

当前 `actions` 只支持：

- 某动作只能打到 `board`
- 某动作只能打到 `entity`
- 某动作只能打到 `event`

这只解决了“目标类型”问题，解决不了“目标语义”问题。

例如：

- `social.replied` 如果只限制 `event`，那么它既能回复 `social.posted`，也能回复 `combat.attacked`
- `social.followed` 如果只限制 `entity`，那么它既能指向 Minecraft 实体，也能指向别的来源实体

所以需要把约束模型拆成两层：

1. `target_types`：粗粒度目标类别
2. `target_constraints`：按目标类型附加细粒度条件

## Recommended Shape

建议 Session action 结构调整为：

```json
[
  {
    "verb": "social.replied",
    "description": "回复帖子或回复",
    "target_types": ["event"],
    "target_constraints": {
      "event": {
        "verb": ["social.posted", "social.replied", "social.quoted"]
      }
    },
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
    "verb": "social.followed",
    "description": "关注 Minecraft 实体",
    "target_types": ["entity"],
    "target_constraints": {
      "entity": {
        "source": ["minecraft"]
      }
    },
    "details_schema": {
      "type": "object",
      "additionalProperties": false
    }
  }
]
```

## Naming Decision

### `target_types`

保留目标类型这一层，但将字段名从 `allowed_target_topologies` 改为 `target_types`。

原因：

- `allowed_target_topologies` 太长
- `Targets` 太泛，看起来像真实目标集合
- `target_types` 最接近“目标类型白名单”的真实语义

### `target_constraints`

`target_constraints` 是一个按目标类型分组的约束字典。

当前只内建两类子约束：

1. `target_constraints.event.verb`
   - 含义：目标 event 的 `verb` 必须在该数组中

2. `target_constraints.entity.source`
   - 含义：目标 entity 的 `source` 必须在该数组中

这里字段名用 `verb` / `source`，但值始终是数组，语义固定为 allowlist。

例如：

- `target_constraints.event.verb = ["social.posted"]`
- `target_constraints.entity.source = ["minecraft", "discord"]`

本设计不使用 `verb_in/source_in` 命名，因为当前只做白名单匹配，直接用短字段更顺手。

## Validation Rules

### Session create / patch

1. `target_types` 必须非空，成员来自固定枚举：`board/event/entity/object`
2. `target_constraints` 可选
3. 如果 `target_constraints.event` 出现，则 `target_types` 必须包含 `event`
4. 如果 `target_constraints.entity` 出现，则 `target_types` 必须包含 `entity`
5. `target_constraints.event.verb` 若存在，必须是非空且去重的 `domain.verb` 数组
6. `target_constraints.entity.source` 若存在，必须是非空且去重的字符串数组

### Event report

事件上报校验顺序调整为：

1. 校验动作 `verb` 已注册
2. 解析 `target_ref` 得到目标类型
3. 校验目标类型在 `target_types` 中
4. 若目标类型为 `event` 且存在 `target_constraints.event.verb`
   - 读取目标 event payload
   - 校验目标 event 的 `verb`
5. 若目标类型为 `entity` 且存在 `target_constraints.entity.source`
   - 读取目标 entity profile
   - 解析其中的 `source`
   - 校验 `source`
6. 校验 `details_schema`

## Metadata Source

### Event target

目标 event 的校验来源是 `EventPayloadRepository.get(event_id)`。

当前只读取最小所需字段：

- `verb`

### Entity target

目标 entity 的校验来源是 `EntityProfileRepository.get(session_id, entity_id)`。

当前只读取最小所需字段：

- `source`

`profile_json` 由客户端注册时写入 Redis，当前已包含 `source`，所以不需要额外建表。

## Error Handling

新增或扩展以下失败原因：

- `target_type_not_allowed`
- `target_event_constraint_mismatch`
- `target_entity_constraint_mismatch`
- `target_event_metadata_unavailable`
- `target_entity_metadata_unavailable`

统一仍走 `422` 业务异常，不把这类失败升级成通用 `404`。

原因：

- 这些校验属于“当前动作契约下请求不合法”
- 服务端并未承诺对所有 `target_ref` 做通用存在性校验
- 只有当某动作声明了额外约束时，服务端才需要解析目标元数据

## Scope

本次只内建：

- `target_constraints.event.verb`
- `target_constraints.entity.source`

本次不做：

- 通用 DSL（如 JSONLogic / CEL）
- `object` / `board` 的细粒度约束
- 范围比较、前缀、正则、否定条件

## Compatibility

这是一次契约变更：

- `allowed_target_topologies` 将被 `target_types` 替换
- 文档、请求 schema、响应 schema、测试和示例都要同步更新

本次不保留双字段兼容，以避免长期混用旧字段名。

## Testing Strategy

至少覆盖：

1. Session action schema
   - 接受 `target_types`
   - 拒绝旧字段 `allowed_target_topologies`
   - 拒绝 `event` 不在 `target_types` 中却声明 `target_constraints.event`
   - 拒绝 `entity` 不在 `target_types` 中却声明 `target_constraints.entity`

2. Event usecase
   - `event.verb` 约束命中时允许
   - `event.verb` 不匹配时拒绝
   - `entity.source` 命中时允许
   - `entity.source` 不匹配时拒绝
   - 目标元数据不可读时拒绝

3. Docs
   - 所有示例字段名统一改为 `target_types`
   - 约束示例统一改为 `target_constraints`
