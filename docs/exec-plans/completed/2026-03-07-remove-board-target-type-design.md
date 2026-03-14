# Board Target Type Removal Design

## 背景

当前系统在两个层面上对“目标类型”有不一致定义：

- Neo4j 物理节点标签只有 `Entity / Event / Object`
- Session action contract 的 `target_types` 却暴露了 `board / event / entity / object`

其中 `board:*` 实际并没有独立的 Neo4j 节点标签，也没有独立的仓储行为。把 `board` 单独放进 `target_types`，会让协议层比底层存储层多出一个没有实体化的类型。

## 决策

将 `board` 从 `target_types` 枚举中移除，统一收敛为 3 种：

- `entity`
- `event`
- `object`

`board:*` 继续作为合法的 `target_ref` 前缀存在，但其基础目标类型视为 `object`。

## 影响

### Session actions

原来：

```json
{
  "verb": "social.posted",
  "target_types": ["board"]
}
```

改为：

```json
{
  "verb": "social.posted",
  "target_types": ["object"]
}
```

### 事件校验

`target_ref` 的基础类型判定规则调整为：

- `event_*` -> `event`
- `entity:<id>` 或裸 `entity_id` -> `entity`
- `board:*` -> `object`
- 其他带前缀引用 -> `object`

### Neo4j

不需要新增或修改图节点标签。

- `board:*` 目标仍然进入 `(:Object {ref: "board:..."})`
- 现有 `Entity / Event / Object` 三类物理节点保持不变

## 为什么不保留 `board`

保留 `board` 的代价大于收益：

- 协议层和存储层概念不一致
- 管理面板和客户端要额外理解“board 是特殊目标类型，但不是物理节点类型”
- 后续若再引入更多对象子类，会继续把 `target_types` 变成业务枚举，而不是基础设施枚举

## 边界

本次仅做“基础目标类型收敛”，不引入新的 `object` 细粒度约束字段。

也就是说：

- `board:*` 仍可作为 `target_ref`
- `target_types` 只做 `object` 级别校验
- 若以后需要区分 `board/object/location/item` 等对象子类，再单独设计 `target_constraints.object.*`

## 预期结果

- `target_types` 枚举只保留 `entity / event / object`
- `board` 不再出现在请求 schema、响应 schema、文档示例和测试断言中
- 现有 `board:*` 事件仍可正常入库，只是会被判定为 `object`
