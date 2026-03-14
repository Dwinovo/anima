# Design Docs

## 概述

本目录保存当前实现口径、架构决策和历史设计演进。Agent 需要先读当前口径文档，再按需参考 legacy 文档了解背景。

## 文档清单

| 文件名 | 摘要 | 最后更新 |
| ------ | ---- | -------- |
| `core-beliefs.md` | 当前版本的产品边界、服务端职责和非目标。 | 2026-03-14 |
| `backend-spec.md` | 后端边界、分层规则、存储职责与服务端约束。 | 2026-03-14 |
| `api-contract.md` | REST 与 WebSocket 契约，包含鉴权和动作 schema 口径。 | 2026-03-14 |
| `postgres-migrations.md` | Alembic 迁移流程、当前 head 与刷新要求。 | 2026-03-14 |
| `legacy-documents.md` | 历史设计文档的使用规则与入口。 | 2026-03-14 |
| `legacy-backend-foundation.md` | 早期后端基础架构稿，保留演进背景。 | 2026-03-06 |
| `legacy-graph-memory-architecture.md` | 早期图谱记忆面设计参考。 | 2026-03-06 |
| `legacy-generalized-entity-decision-architecture.md` | 泛实体决策模型历史稿。 | 2026-03-06 |
| `legacy-entity-lifecycle-architecture.md` | 泛实体生命周期历史稿。 | 2026-03-06 |
| `legacy-animation-technical-architecture.md` | 早期 Animation 技术架构稿。 | 2026-03-06 |

## 相关链接

- [架构总览](../../ARCHITECTURE.md)
- [产品规格目录](../product-specs/index.md)
- [执行计划目录](../exec-plans/index.md)
- [文档总入口](../index.md)
