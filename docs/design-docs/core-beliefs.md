# Core Beliefs

## 概述

Anima 当前不是“托管推理平台”，而是一个稳定的 Entity Activity Network 后端内核。服务端负责协议、生命周期、校验、存储与查询；智能策略继续留在客户端或上层编排器。

## 核心要点

- `Edge Mind + Server Bus` 是当前架构基线。
- 服务端聚焦四件事：
  - `Context Assembly`
  - `Gatekeeper Validation`
  - `Persistence & Query`
  - `Token Issuance & Replay Guard`
- 领域统一使用 Activity 语义，工程实现继续保留 `Event` 命名以兼容当前代码。
- Session 是隔离边界；`Session.actions` 是动作注册表；Entity 通过会话级 token 访问写接口。
- 仓库是唯一事实源。任何不在仓库里的约定，对 Agent 来说都视为不存在。

## 约束

- 服务端不负责中心化调度、托管推理、模型密钥代管。
- 服务端不维护全局动作白名单；动作合法性只在 Session 作用域内校验。
- 服务端不对 `target_ref` 引入额外的产品语义约束，除非有新的设计决策文档明确批准。
- 文档结构必须保持“入口小、索引清晰、按需深入”的渐进式披露方式。

## 相关文件

- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [backend-spec.md](./backend-spec.md)
- [api-contract.md](./api-contract.md)
- [../product-specs/product-vision.md](../product-specs/product-vision.md)
- [../SECURITY.md](../SECURITY.md)
