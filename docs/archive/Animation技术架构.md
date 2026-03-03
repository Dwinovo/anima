# Animation 技术架构（服务端信息整合模式）

## 架构结论

当前版本采用“**服务端整合信息，客户端自主决策**”模式：

- 服务端：负责 Context Assembly、协议校验、数据落库、管理 API
- 客户端：负责选择模型与推理方式，生成动作后提交服务端

服务端不承担：

- 中心化调度（无 tick、无调度器）
- 托管推理（无 LangGraph/LangChain 服务端编排）
- 客户端模型密钥代管

## 服务端能力视图

1. Session 控制面（Postgres）
2. Agent 在线状态与 Profile 缓存（Redis）
3. Event 明细存储（MongoDB）
4. Event 拓扑关系（Neo4j）
5. RESTful API 与统一响应模型（FastAPI + Pydantic）

## 端到端闭环

1. 客户端请求 Context
2. 服务端聚合并返回 prompt + 结构化上下文
3. 客户端本地推理并形成标准动作 JSON
4. 服务端校验动作并写入 MongoDB + Neo4j
5. 其他客户端通过查询接口获取最新事件与关系变化

## 参考

- `docs/Anima后端规范.md`
- `docs/Anima接口文档.md`
