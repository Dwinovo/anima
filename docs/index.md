# Documentation Map

## 概述

本仓库把“Anima 是什么、现在做到哪一步、下一步该做什么”全部收敛到版本控制内。Agent 进入项目后，应从这里开始，再按需深入到具体设计、规格、计划与参考资料。

## 核心要点

- 当前产品定位是 `Entity Activity Network` 后端内核，而不是托管推理平台。
- 当前仓库是单仓前后端项目：后端位于 `../backend/`，管理台前端位于 `../apps/admin/`。
- 文档体系分为五类：
  - `design-docs/`：当前实现口径与架构决策
  - `product-specs/`：面向客户端与控制面的规格
  - `exec-plans/`：计划、归档和技术债务
  - `generated/`：从代码结构导出的快照
  - `references/`：关键外部依赖的 LLM 友好说明
- 推荐阅读顺序：
  1. `../ARCHITECTURE.md`
  2. `FRONTEND.md`
  3. `design-docs/core-beliefs.md`
  4. `design-docs/backend-spec.md`
  5. `design-docs/api-contract.md`
  6. `product-specs/index.md`
  7. `exec-plans/index.md`

## 约束

- 入口文档应保持短而稳定；细节下沉到子目录与专题文档。
- 所有新增文档都要进入最近的 `index.md`。
- 生成产物放在 `generated/`，不要与手写文档混放。
- 历史方案保留在 `design-docs/legacy-*`，但不作为当前实现依据。
- 当前完整后端工程位于 `../backend/`，管理台前端位于 `../apps/admin/`；根目录只保留仓库级入口和共享配置。

## 相关文件

- [../AGENTS.md](../AGENTS.md)
- [../ARCHITECTURE.md](../ARCHITECTURE.md)
- [FRONTEND.md](./FRONTEND.md)
- [design-docs/index.md](./design-docs/index.md)
- [product-specs/index.md](./product-specs/index.md)
- [exec-plans/index.md](./exec-plans/index.md)
- [generated/index.md](./generated/index.md)
- [references/index.md](./references/index.md)
