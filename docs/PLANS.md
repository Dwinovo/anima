# Plans

## 概述

项目当前处于“后端契约稳定化 + 管理台同仓落地 + Agent 可交接化”阶段。核心协议已经收敛到 Session / Entity / Event / Context 主链路，接下来重点是把管理台从脚手架推进到可用控制面，并继续补齐知识地图、生成快照与运行标准。

## 核心要点

- 当前阶段
  - 稳定服务边界：保持服务端只做协议、校验、存储、查询与鉴权。
  - 稳定 monorepo 结构：让 `apps/admin` 和 `backend/` 在同一仓库内协同演进。
  - 稳定知识入口：让 Agent 只靠仓库文档就能接手。
  - 稳定存储快照：避免 schema、迁移和代码脱节。
- 近期计划
  - 为 `apps/admin` 落地 `/sessions` 列表、详情和事件流页面。
  - 明确前端的数据访问、构建和测试约定。
  - 自动化生成 `docs/generated/` 快照。
  - 增强架构边界测试与安全/可靠性检查。
  - 衔接管理台与客户端规格的实现验证。
- 中期计划
  - 丰富观测能力与运维约束。
  - 根据真实使用场景扩展更多 verb 域与上下文视图，但不破坏当前边界。

## 约束

- 新计划应优先放入 `docs/exec-plans/active/`，完成后移入 `completed/`。
- 任何规划文档都不能绕过现有核心边界：服务端不是推理引擎。
- 前端范围以 `docs/FRONTEND.md` 和 `docs/product-specs/admin-console-spec.md` 为准，不要让脚手架页面代替规格。
- 若计划会改变资源词汇或分层方向，必须先更新 `ARCHITECTURE.md` 与相关设计文档。

## 相关文件

- [exec-plans/index.md](./exec-plans/index.md)
- [exec-plans/tech-debt-tracker.md](./exec-plans/tech-debt-tracker.md)
- [QUALITY_SCORE.md](./QUALITY_SCORE.md)
- [PRODUCT_SENSE.md](./PRODUCT_SENSE.md)
