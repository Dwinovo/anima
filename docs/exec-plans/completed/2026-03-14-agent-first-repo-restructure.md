# Agent-First Repo Restructure

## 概述

本计划记录 2026-03-14 对仓库文档结构的重构：把原先“散落在 `docs/` 根目录、archive、plans` 中的面向人阅读文档”，重组为面向 Agent 的稳定入口与分层索引。

## 核心要点

- 已完成的调整
  - 新增根入口：`AGENTS.md`、`ARCHITECTURE.md`
  - 创建结构化目录：
    - `docs/design-docs/`
    - `docs/product-specs/`
    - `docs/exec-plans/active/`
    - `docs/exec-plans/completed/`
    - `docs/generated/`
    - `docs/references/`
  - 将原 `docs/archive/` 文档迁移为 `design-docs/legacy-*`
  - 将原 `docs/plans/` 文档迁移到 `docs/exec-plans/completed/`
  - 将原散落的中文文件重命名为 kebab-case 英文文件名
  - 补齐索引、技术债务、路线图、安全、可靠性、质量评分和依赖参考
- 设计决策
  - 入口文档尽量短，细节下沉到 `docs/`
  - 历史文档不删除，但明确标成 legacy
  - `generated/` 与 `references/` 分离：前者是项目快照，后者是外部依赖知识

## 约束

- 后续新增文档必须进入最近的 `index.md`。
- 若 `generated/` 内容刷新方式改变，应在 `tech-debt-tracker.md` 里同步更新状态。
- 若结构再调整，需要同步更新 `AGENTS.md` 与 `docs/index.md`。

## 相关文件

- [../../index.md](../../index.md)
- [../../../AGENTS.md](../../../AGENTS.md)
- [../../../ARCHITECTURE.md](../../../ARCHITECTURE.md)
- [../tech-debt-tracker.md](../tech-debt-tracker.md)
