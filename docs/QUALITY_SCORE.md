# Quality Score

## 概述

本评分以 `1-5` 计分：`1` 表示高风险且缺少基本护栏，`5` 表示约束清晰、测试充分、交接成本低。分数不是奖惩，而是帮助 Agent 快速判断“哪里最需要继续投入”。

## 核心要点

| 领域 | 分数 | 证据 | 差距 | 改进方向 |
| ---- | ---- | ---- | ---- | -------- |
| 架构边界 | `4/5` | `backend/src/` 分层清晰，且有架构测试保护旧 `agent` 依赖迁移。 | 还缺 application / infrastructure 的更全面边界测试。 | 增加 import guard 与组合根约束测试。 |
| API 契约 | `4/5` | 路由暴露面、schema 校验、异常映射都有对应测试。 | 契约快照未自动导出，仍主要靠代码和文档对照。 | 增加 API schema 生成与契约 smoke checks。 |
| Entity 鉴权与会话安全 | `4/5` | 有 access / refresh、token_version、防重放设计和测试。 | 安全策略尚未通过 CI 级检查显式守护。 | 把关键安全路径加入更强验证。 |
| Event 持久化链路 | `4/5` | 写入顺序明确，Mongo + Neo4j 双写规则有用例测试支撑。 | 缺少更明确的失败补偿与运维说明。 | 补失败场景说明与运维手册。 |
| 文档与 Agent 可交接性 | `3/5` | 现在已有入口、索引、计划、债务、参考资料。 | `generated/` 仍是人工维护，部分旧文档仍保留历史写法。 | 自动化生成快照，逐步统一关键文档结构。 |
| 可靠性与运维 | `3/5` | 启动依赖检查、基础测试与清晰的运行边界已经存在。 | 观测、告警、恢复流程仍偏轻。 | 扩充日志字段、指标与 runbook。 |
| 前端/管理台落地一致性 | `2/5` | `apps/admin/` 已创建 Next.js 工程，并已纳入 monorepo。 | 当前仍是脚手架首页，缺少 Session 页面、数据访问约定和前端测试。 | 按 `admin-console-spec.md` 落地 `/sessions` 与详情页，并补 lint、build、测试约束。 |

## 约束

- 评分应以仓库内证据为准，不凭感觉打分。
- 分数变化时，应同步更新原因与下一步动作。
- 若某项风险进入执行阶段，应在 `docs/exec-plans/` 中有对应计划或记录。

## 相关文件

- [PLANS.md](./PLANS.md)
- [exec-plans/tech-debt-tracker.md](./exec-plans/tech-debt-tracker.md)
- [RELIABILITY.md](./RELIABILITY.md)
- [SECURITY.md](./SECURITY.md)
