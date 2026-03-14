# Monorepo Frontend Docs Design

## 概述

`apps/admin/` 已经进入仓库，但入口文档、状态文档和产品规格里仍有多处把前端描述成“未入仓”或“外部实现”。这次调整的目标是把仓库口径统一成单仓前后端项目，并把 Next.js 的忽略规则收回根目录 `.gitignore`。

## 核心要点

- 仓库地图改为 `apps/admin/` + `backend/` 的 monorepo 视角。
- `AGENTS.md`、`ARCHITECTURE.md`、`docs/index.md`、`docs/FRONTEND.md` 负责更新入口认知。
- `docs/product-specs/admin-console-spec.md`、`docs/PLANS.md`、`docs/QUALITY_SCORE.md`、`docs/PRODUCT_SENSE.md`、`docs/exec-plans/tech-debt-tracker.md` 负责更新当前状态和后续方向。
- `apps/admin/.gitignore` 的规则并入根目录 `.gitignore`，避免在 monorepo 里出现双份忽略入口。

## 约束

- 这次只做文档与忽略规则迁移，不修改 `apps/admin` 的运行行为。
- 前端与后端的边界仍是 HTTP API，不引入共享运行时代码。
- 根目录 `.env` 继续作为当前后端默认运行时环境文件。

## 相关文件

- [../../../AGENTS.md](../../../AGENTS.md)
- [../../../ARCHITECTURE.md](../../../ARCHITECTURE.md)
- [../../FRONTEND.md](../../FRONTEND.md)
- [../../product-specs/admin-console-spec.md](../../product-specs/admin-console-spec.md)
- [../../../.gitignore](../../../.gitignore)
- [../../../apps/admin/package.json](../../../apps/admin/package.json)
