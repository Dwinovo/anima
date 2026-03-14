# Product Sense

## 概述

Anima 的产品方向不是替 Entity 做统一决策，而是为多种实体提供一个稳定、可扩展、可记录的活动网络底座。它服务的首先是“需要统一协议与记忆面”的系统，而不是“需要中心化智能编排”的系统。

## 核心要点

- 目标用户
  - 构建多 Entity 世界或仿真系统的后端工程师
  - 需要统一接入 AI Entity、脚本客户端、设备节点的基础设施团队
  - 需要查看 Session 活动流与运行状态的运营/管理角色
- 核心价值
  - 用统一 Activity 协议替代零散的场景特化事件模型
  - 用稳定的服务边界把“协议/状态底座”和“策略/推理”分开
  - 用多存储协作支撑控制面、运行态、事件载荷和图谱查询
  - 用单仓管理减少控制面前端和后端契约之间的漂移
- 北极星指标
  - 新实体接入时间是否缩短
  - Session 内事件协议是否稳定、可演进
  - Context 返回是否足够支持客户端本地决策
  - 文档是否足够让新 Agent 或新工程师独立接手

## 约束

- 不把服务端演变成托管模型平台。
- 不为了追求“通用世界引擎”而提前引入复杂抽象。
- 管理面板是控制面，不是推理平台。

## 相关文件

- [product-specs/product-vision.md](./product-specs/product-vision.md)
- [product-specs/entity-client-spec.md](./product-specs/entity-client-spec.md)
- [product-specs/admin-console-spec.md](./product-specs/admin-console-spec.md)
- [PLANS.md](./PLANS.md)
