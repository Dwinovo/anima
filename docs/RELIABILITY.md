# Reliability

## 概述

Anima 的可靠性重点不在“永不失败”，而在“边界明确、失败可见、状态可恢复”。当前后端通过启动检查、清晰的持久化职责和测试覆盖来维持这一点。

## 核心要点

- 启动阶段
  - Redis、MongoDB、Postgres、Neo4j 会在应用启动时做连通性检查。
  - 若检查失败，服务会记录错误日志，但当前实现仍继续启动。
- 运行阶段
  - Session 控制面以 Postgres 为真相源。
  - Event 上报遵守“先 Mongo 载荷、后 Neo4j 骨架”的双写顺序。
  - Presence 断开时，会清理在线态、心跳和相关 token 状态。
- 验证阶段
  - 路由暴露面、schema、use case、键名和图谱 schema 都有测试覆盖。
  - 可靠性相关约束需要继续沉淀为更显式的 runbook 与 smoke checks。

## 约束

- 不要把启动检查失败解释成“服务健康”；它只表示当前策略允许继续运行。
- 改动持久化顺序、Presence 清理或 token 生命周期前，必须同步更新测试和本文件。
- 新的运行时依赖若加入启动路径，需要在 `backend/src/main.py` 和本文件同时登记。

## 相关文件

- [../ARCHITECTURE.md](../ARCHITECTURE.md)
- [design-docs/backend-spec.md](./design-docs/backend-spec.md)
- [generated/db-schema.md](./generated/db-schema.md)
- [exec-plans/tech-debt-tracker.md](./exec-plans/tech-debt-tracker.md)
