# Security

## 概述

当前安全模型围绕“会话级 Entity 身份”展开：Entity 注册后拿到 access / refresh token，对写接口与 WebSocket 心跳通道进行访问；refresh token 采用单次消费并带有重放防护。

## 核心要点

- 认证与授权
  - HTTP 写接口要求 `Authorization: Bearer <access_token>`。
  - WebSocket Presence 使用 query 参数 `access_token`。
  - `report_event` 会同时校验 token 中的 `entity_id` 与请求体中的 `subject_uuid` 是否一致。
- 令牌状态
  - `access_token` 是短时凭证。
  - `refresh_token` 单次消费，按 `refresh_jti` 跟踪。
  - 发现重放后，通过提升 `token_version` 让旧 token 失效。
- 状态清理
  - Entity 下线或 Presence 断连时，相关在线态和鉴权状态会被清理。
- 密钥管理
  - 服务端只持有自己的签名密钥，不托管客户端模型 API Key。

## 约束

- 不要把 refresh token 设计成可重复使用。
- 不要让服务端承担客户端模型凭据管理。
- 新增写接口时，必须明确它使用 Entity 级还是 Session 级 access claims。
- 若安全规则改变，必须同步更新 API 契约、测试和本文件。

## 相关文件

- [design-docs/api-contract.md](./design-docs/api-contract.md)
- [design-docs/backend-spec.md](./design-docs/backend-spec.md)
- [../ARCHITECTURE.md](../ARCHITECTURE.md)
- [../backend/src/presentation/api/dependencies.py](../backend/src/presentation/api/dependencies.py)
