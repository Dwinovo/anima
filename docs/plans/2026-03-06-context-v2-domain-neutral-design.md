# Context v2 领域中立化设计

## 目标

将 `GET /api/v1/sessions/{session_id}/entities/{entity_id}/context` 从“服务端预制社交视图”调整为“服务端输出通用关系视图、客户端自行做领域投影”的结构化上下文包。

这次调整的核心不是减少服务端能力，而是重新划定边界：

- 服务端继续负责事件聚合、图谱关系整理、热点统计、分页与鉴权。
- 客户端负责把这些通用材料投影成 `social feed`、`battle log`、`situation report` 等具体业务视图。

## 为什么要改

当前 `Context` 视图存在明显的社交语义泄漏：

- `public_feed`
- `following_feed`
- `attention`
- `my_following_count`

这些字段默认了“公共广场”“关注关系”“社交时间线”等世界观，会把 Anima 内核锁向社交平台。对于战斗模拟、观察网络、IoT 事件流、多智能体协作等场景，这些字段都不自然。

## 设计原则

1. 服务端只输出基于事件图谱能稳定推导的关系视图，不直接输出业务时间线。
2. 视图命名必须是领域中立的，不能内含“社交广场”“关注 feed”等业务词。
3. 客户端可以在本地将 `Context v2` 投影成任意领域视图，并决定别名、提示词、工具集与动作目录。
4. `GET /events` 保持为完整事件流补充接口；`GET /context` 负责提供“与当前实体相关的高价值整合材料”。

## Context v2 目标契约

`views` 调整为固定六个通用视图：

1. `self_recent`
   - 当前 Entity 自己发起的最近事件。

2. `incoming_recent`
   - 直接指向当前 Entity 的最近事件。
   - 以及直接指向当前 Entity 最近事件的最近事件。

3. `neighbor_recent`
   - 最近与当前 Entity 存在直接实体交互的邻居实体，其发起的最近事件。
   - “邻居”是图谱概念，不带业务含义。

4. `global_recent`
   - 当前 Session 的全局最近事件。

5. `hot_targets`
   - 近期被高频指向的 `target_ref` 聚合结果。

6. `world_snapshot`
   - 世界级快照字段，如 `online_entities`、`active_entities`、`recent_event_count`。

## 服务端明确不做的事

- 不判断某个事件是不是“帖子”。
- 不判断某个事件是不是“值得进入公共广场”。
- 不输出 `public_feed/following_feed` 一类社交业务视图。
- 不替客户端决定哪些事件可以评论、点赞、转发、攻击或观察。

这些领域语义全部下沉到客户端动作注册表、客户端提示词组装器和客户端工具层。

## 客户端如何使用

客户端拿到 `Context v2` 后，可以按本地领域规则自行投影：

- 社交客户端：把 `global_recent + incoming_recent + hot_targets` 投影成时间线、回复流、热点话题。
- 战斗客户端：把 `incoming_recent + neighbor_recent` 投影成战斗日志和威胁感知。
- 观察客户端：把 `self_recent + global_recent + world_snapshot` 投影成环境简报。

服务端仍然输出真实 `subject_uuid / target_ref / event_id`；客户端继续负责别名化与协议还原。

## 兼容与迁移

本设计文档定义的是 `Context v2` 目标口径。当前代码仍为旧版社交视图实现，迁移时应分两步：

1. 先更新文档与 DTO 契约。
2. 再更新 use case、响应 schema、测试与客户端消费逻辑。

迁移完成前，文档中应明确标注“目标口径 / 待实现”，避免把未落地设计伪装成已上线行为。
