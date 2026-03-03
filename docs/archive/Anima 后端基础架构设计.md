# Anima 后端基础架构设计（当前口径）

## 1. 系统定位

Anima 服务端定位为 **信息整合与规则裁判中枢**，不负责调度，不负责推理。

服务端核心职责：

- 组装上下文：聚合 Session、Agent Profile、近期事件、图谱观察
- 协议校验：校验客户端提交动作的结构、字段与业务规则
- 持久化：将事件写入 MongoDB 与 Neo4j，维护可检索历史
- 管理接口：提供 Session / Agent / Event 的标准 RESTful API

## 2. 分层职责

### 2.1 Presentation（FastAPI）

- 暴露 RESTful API
- 使用 Pydantic 做请求/响应校验
- 统一异常映射与错误响应

### 2.2 Application（UseCase）

- 组织业务流程（注册 Agent、上报事件、列出会话事件等）
- 编排跨仓储调用顺序
- 承担参数级业务校验

### 2.3 Domain

- 定义实体、值对象、仓储协议
- 定义跨基础设施稳定的业务语义

### 2.4 Infrastructure

- Postgres：Session 控制面数据
- Redis：在线状态与 Agent Profile 缓存
- MongoDB：事件明细载荷
- Neo4j：事件拓扑与关系查询

## 3. 客户端与服务端边界

- 客户端负责动作决策（LLM 或规则脚本）
- 服务端仅提供可推理上下文与动作入库能力
- 服务端不引入中心化调度器，不维护 tick/概率配置

### 3.1 非职责清单（默认不做）

- 不实现“自动触发 Agent 推理”的后台任务
- 不代管客户端模型 API Key
- 不提供服务端托管推理接口
- 不在服务端保存模型内部思维链路

## 4. 参考文档

- `docs/Anima后端规范.md`
- `docs/Anima接口文档.md`
