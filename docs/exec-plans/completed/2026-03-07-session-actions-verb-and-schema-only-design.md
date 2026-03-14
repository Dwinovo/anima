# Session Actions Verb-And-Schema-Only Design

## 背景

当前 `Session.actions` 已经扩展出两层目标限制：

- `target_types`
- `target_constraints`

这使服务端开始承担“某个 verb 应该指向什么目标”的产品语义判断。对当前的 Anima 定位来说，这层约束过重。

当前定位更接近：

- 服务端：图谱关系与信息整合模块
- 客户端：决定社交/战斗/观察等产品语义，并发出真实事件

在这个边界下，服务端继续强限制 `target_ref` 的走向，会让基础设施逐渐收缩成某一种上层产品规则。

## 决策

将 `Session.actions` 收敛为最小稳定合同，只保留：

- `verb`
- `description`
- `details_schema`

移除：

- `target_types`
- `target_constraints`

## 新语义

### Session action

```json
{
  "verb": "social.posted",
  "description": "发布内容",
  "details_schema": {
    "type": "object",
    "required": ["content"],
    "properties": {
      "content": {"type": "string", "minLength": 1}
    },
    "additionalProperties": false
  }
}
```

### 服务端写入校验

保留：

1. Session 存在
2. Subject Entity 存在
3. `verb` 已注册在当前 `Session.actions`
4. `details` 通过该动作的 `details_schema`
5. 鉴权合法

移除：

1. `target_ref` 基础目标类型校验
2. `target_constraints.event.verb`
3. `target_constraints.entity.source`
4. 所有“这个 verb 只能指向某类目标”的服务端语义限制

## 结果

`target_ref` 继续存在，但对服务端而言变成不透明目标引用：

- 可以是 `entity:...`
- 可以是 `event_...`
- 可以是 `board:...`
- 可以是其他对象引用

服务端会把它入库、建图、返回给客户端，但不负责判定“它该不该被这个 verb 指向”。

## 为什么这样更合理

### 更符合基础设施定位

服务端只保证：

- 动作名称合法
- 载荷结构合法
- 事件可以被存储和查询

而不是决定世界里的所有关系语义。

### 减少协议膨胀

若继续走 `target_constraints` 路线，后续会自然演变成：

- `event.verb`
- `entity.source`
- `object.kind`
- `entity.tags`
- `event.tags`

这会让 action contract 逐渐变成一个半成品规则引擎。

### 保留上层自由度

客户端或上层应用仍然可以自主决定：

- 评论什么事件
- 攻击什么实体
- 把什么 object 当作 board/location/item

只是这些语义不再由基础设施服务端强制。

## 兼容性

- 旧的 `target_types` / `target_constraints` 字段不再出现在新的请求和响应 schema 中
- 旧 Session 若持久化过这些字段，读取时会被忽略，不参与运行时校验
- 一旦 Session 被重新保存，序列化结果只会保留 `verb / description / details_schema`

## 非目标

本次不移除：

- `target_ref` 字段本身
- Neo4j 中的 `Entity / Event / Object` 图谱骨架
- `details_schema` 校验
- `verb` 注册表
