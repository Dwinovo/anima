# AGENTS.md

## 项目身份

Anima 是一个单仓管理的前后端项目：`backend/` 提供 Entity Activity Network 后端内核，`apps/admin/` 提供基于 Next.js 的管理台前端。

## 知识库索引

- [ARCHITECTURE.md](ARCHITECTURE.md)：顶层模块地图、依赖方向、关键请求路径。
- [docs/index.md](docs/index.md)：文档总入口与推荐阅读顺序。
- [docs/FRONTEND.md](docs/FRONTEND.md)：`apps/admin` 的前端结构、职责边界和当前状态。
- [docs/design-docs/core-beliefs.md](docs/design-docs/core-beliefs.md)：当前版本的核心理念与非目标。
- [docs/design-docs/backend-spec.md](docs/design-docs/backend-spec.md)：服务边界、分层职责、存储职责。
- [docs/design-docs/api-contract.md](docs/design-docs/api-contract.md)：REST/WebSocket 契约与字段口径。
- [docs/product-specs/index.md](docs/product-specs/index.md)：客户端、管理台、产品愿景等规格文档。
- [docs/exec-plans/index.md](docs/exec-plans/index.md)：执行计划、完成归档、技术债务入口。
- [docs/exec-plans/tech-debt-tracker.md](docs/exec-plans/tech-debt-tracker.md)：当前已知技术债务，按优先级排序。
- [docs/RELIABILITY.md](docs/RELIABILITY.md)：可靠性标准、失败处理和运行约束。
- [docs/SECURITY.md](docs/SECURITY.md)：鉴权、重放防护、密钥与边界约束。
- [docs/QUALITY_SCORE.md](docs/QUALITY_SCORE.md)：按模块划分的质量评分与改进方向。
- [docs/generated/db-schema.md](docs/generated/db-schema.md)：当前存储结构快照。
- [docs/references/index.md](docs/references/index.md)：关键外部依赖的 LLM 友好参考。

## 架构速览

- 仓库主线是 `apps/admin -> HTTP API -> backend/src/presentation -> backend/src/application -> backend/src/domain`。
- `apps/admin` 只通过 API 契约与 `backend/` 协作，不直接依赖 Python 实现细节。
- `backend/src/infrastructure` 负责实现 `backend/src/domain` 定义的仓储与安全协议，并由 `backend/src/presentation/api/dependencies.py` 作为组合根进行装配。
- `backend/src/domain` 不得依赖 FastAPI、SQLAlchemy、Redis、MongoDB、Neo4j 等框架或 SDK。

## Agent 行为约束

- 不要手动修改 `docs/generated/` 下的文件；需要先更新源代码或生成过程，再刷新快照。
- 新增文档后，必须在最近的 `index.md` 注册；若改变文档地图，也要同步更新本文件。
- 代码修改必须保持依赖方向：`presentation -> application -> domain <- infrastructure`。
- `apps/admin` 与 `backend/` 通过 HTTP 契约协作，不要建立跨语言的私有运行时耦合。
- 根目录 `.env` 是当前默认运行时环境文件；示例配置位于 `backend/.env.example`。
- 前端忽略规则统一维护在根目录 `.gitignore`；没有明确理由时，不要重新添加 `apps/admin/.gitignore`。
- 不要在服务端重新引入“动作目标语义裁判”；当前 `Session.actions` 只校验 `verb` 与 `details_schema`。
- `Session`、`Entity`、`Event`、`Context` 是当前公共资源词汇，除非有明确计划文档，不要擅自改名。
- 修改代码前先读相关文档；宣称完成前必须运行与改动范围匹配的 lint / tests。
- 当文档与代码冲突时，以代码和测试为准，并在同一改动中修正文档。

## 快速入门

1. 先读 [docs/index.md](docs/index.md) 和 [ARCHITECTURE.md](ARCHITECTURE.md)。
2. 再打开最接近任务的规格或计划文档：`docs/design-docs/`、`docs/product-specs/`、`docs/exec-plans/`。
3. 最后按任务进入对应工程：后端改动在 `backend/` 中处理，管理台改动在 `apps/admin/` 中处理。
