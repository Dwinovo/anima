# Tech Debt Tracker

## 概述

本文件记录当前已知技术债务。优先级按 `P0` 到 `P3` 递减，`P0` 表示会持续影响架构正确性或团队交接效率。

## 核心要点

| 优先级 | 债务项 | 现状 | 建议动作 |
| ------ | ------ | ---- | -------- |
| `P0` | 生成文档尚未自动化 | `docs/generated/db-schema.md` 现在是人工维护快照，容易漂移。 | 增加脚本，从 SQLAlchemy 模型、Alembic、Redis/Neo4j 常量自动生成。 |
| `P1` | 文档与代码仍可能再次漂移 | 过去已经出现 Alembic 文档落后于真实 migration head。 | 将 schema/doc 刷新加入发布或 CI 检查。 |
| `P1` | 观测能力入口已建但尚未形成统一标准 | `backend/src/infrastructure/observability/` 存在，但没有统一日志字段和指标清单。 | 明确日志字段、错误分类和基础指标，并补测试或 smoke checks。 |
| `P1` | 架构约束测试覆盖面有限 | 当前只有少量边界测试，无法完整保护分层规则。 | 增加 application / infrastructure 反向依赖测试与 import guard。 |
| `P2` | 管理台已入仓，但前端能力仍停留在脚手架阶段 | `apps/admin/` 已存在 Next.js 工程，但还没有 Session 页面、数据访问层和测试；Entity 客户端仍只有规格。 | 先按管理台规格落地控制面页面，再补前端运行/验证指南，并明确客户端实现位置。 |
| `P2` | 安全与可靠性策略刚完成文档化 | 规则已整理，但还没有 CI 级强校验。 | 把关键约束转成 tests / checks，例如 token 失效链路、启动依赖策略。 |
| `P3` | 文档语言与命名风格仍有中英混合 | 入口结构已经统一，但内容层仍保留历史写法。 | 后续按需渐进清理，不要为了统一而大规模重写有效文档。 |

## 约束

- 新发现的技术债务必须直接追加到本文件，不要只写在提交说明或聊天里。
- 若某项债务开始执行，应在对应执行计划里引用本文件中的条目。
- 若债务已偿还，应删除或移动到相关完成计划中并保留简短说明。

## 相关文件

- [index.md](./index.md)
- [completed/index.md](./completed/index.md)
- [../QUALITY_SCORE.md](../QUALITY_SCORE.md)
- [../PLANS.md](../PLANS.md)
