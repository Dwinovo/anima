为了支撑泛实体的“社交基座”，后端采用了分层治理的架构。各组件通过 `session_id` 实现多租户隔离，确保时空边界的严整。
## 1. FastAPI：神经中枢与资源网关

FastAPI 负责处理所有来自 Sensor 的 RESTful 请求，是整个 Brain 的唯一入口。
- **职责范围**：
    - **路由分发**：实现 Session 管理、Agent 注册/卸载及 Event 事件上报的 RESTful 接口。
    - **鉴权与流控**：根据 PostgreSQL 中的世界配置，校验请求合法性并执行 `max_agents_limit` 配额检查。
    - **异步调度**：利用 Python 的 `asyncio` 异步特性，并发处理 LLM 推理等高延迟任务。
    - **协议校验**：通过 Pydantic 模型严格校验 Sensor 传来的主谓宾三元组 JSON。
## 2. LangGraph：认知编排与短期记忆

LangGraph 负责为泛实体注入“灵魂”，是处理 Agent 认知流转的核心状态机。
- **职责范围**：
    - **有状态推理**：编排 Agent 从读取 Profile、检索记忆到生成决策的完整逻辑流。
    - **短期记忆管理 (Checkpointer)**：负责存储 Agent 过去几分钟内的对话流和思考状态。
    - **决策流转**：决定 LLM 输出的内容
- **清理逻辑**：在 Agent 卸载时，负责清空对应的工作台状态；在 Session 硬删除时，抹除该世界下所有实体的推理快照。

## 3. Redis：实时状态与在线中心

Redis 充当系统的“热数据层”，负责维护当前世界的瞬时脉搏。

- **职责范围**：
    - **在线状态 (Presence)**：通过 Set 结构存储 `active_agents` 集合，实时回答“谁在线”的问题。
    - **灵魂缓存 (Profile Cache)**：以 Hash 结构存储 Agent 的 Profile 数据，避免在推理时频繁读取关系型数据库。
    - **高频变量**：存储实体的瞬时情绪值、意图评分等不需要持久化到图谱的变动数据。
- **清理逻辑**：
    - **Agent 卸载**：仅删除该 `uuid` 的特定缓存键值。
    - **Session 硬删除**：按 `sessionid:uuid` 命名空间前缀批量删除（例如：`DEL anima:agent:srv-001:*`），瞬间清理整个世界的运行态数据。
## 4. PostgreSQL：控制面配置基座

PostgreSQL 存储 `sessions`（Session 表），是整个 Anima 系统的元数据锚点。
- **职责范围**：
    - **静态配置**：存储世界的名称、描述（全局 Context）、默认 LLM 类型及资源配额（`max_agents_limit`）。
    - **审计追踪**：记录创世时间 `created_at` 与最后更新时间。
- **清理逻辑**：执行 Session 硬删除时，物理删除对应的记录，作为整个级联删除流程的起点。
## 基础设施职责汇总表

|**组件**|**数据类型**|**存储时长**|**Agent 卸载动作**|**Session 删除动作**|
|---|---|---|---|---|
|**FastAPI**|无 (逻辑层)|瞬时|拦截离线请求|销毁路由上下文|
|**LangGraph**|JSON (工作记忆)|短期|**清空工作台**|物理清空全部 Checkpoint|
|**Redis**|Key-Value (状态)|中短期|**移除在线状态与缓存**|**批量前缀删除**|
|**PostgreSQL**|Relational (配置)|长期|无动作|**物理删除记录**|
|**Neo 4 j**|Graph (社交记忆)|永久/Session 级|**严禁删除 (保留遗迹)**|**物理清空图谱**|
