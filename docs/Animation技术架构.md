# Anima后端基础架构设计
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
    - **Session 硬删除**：通过 `session_id` 前缀批量删除（`DEL session:{id}:*`），瞬间清理整个世界的运行态数据。
## 4. PostgreSQL：控制面配置基座

PostgreSQL 存储“世界表” `worlds`，是整个 Anima 系统的元数据锚点。
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
|**Neo4j**|Graph (社交记忆)|永久/Session级|**严禁删除 (保留遗迹)**|**物理清空图谱**|
# Anima 泛实体生命周期与架构设计文档

**系统定位：** 作为 Anima 系统的云端基座（Brain），负责接管并调度异构客户端（Sensor）的事件接入、鉴权、状态流转与基于大模型（LLM）的认知推理。 **核心设计原则：**
1. **RESTful 资源导向：** 一切交互皆为资源状态的转移（Session, Agent, Event）。
2. **状态纯粹化：** 摒弃底层物理躯壳属性（如血量、电量），专注管理泛实体的“灵魂（Profile）”。
3. **惰性图谱构建 (Lazy Initialization)：** 绝不在实体无交互时消耗图数据库资源，使用 `MERGE` 策略按需固化记忆。
4. **存储分层：** 控制面走关系型数据库（如 PostgreSQL），热状态与在线集走 Redis，工作记忆走 LangGraph，长程羁绊走 Neo4j。
## 第一部分：宏观世界生命周期 (The Session Lifecycle)

Session（世界/平台）是 Anima 社交网络的顶级容器。它决定了泛实体们所处的平行时空边界。
### 数据字典 (Data Dictionary)

表名：`worlds`

|**字段名称**|**数据类型**|**约束条件**|**默认值**|**业务含义与作用**|
|---|---|---|---|---|
|**`session_id`**|String(64)|Primary Key, Index|自动生成 (如 `world_xxx`)|**隔离边界与寻址标识。** 系统的顶级路由键。Redis 中的活跃集合、Neo4j 中的记忆图谱，均依赖此 ID 进行硬隔离。|
|**`name`**|String(100)|Not Null|无|**世界名称。** 面向人类管理员的易读标识（如：`Cyberpunk-City-01` 或 `Minecraft-Server-A`）。|
|**`description`**|Text|Nullable|Null|**世界观设定 (Global Context)。** 极具战略价值的字段。该内容会在运行时作为全局背景注入到大模型的 System Prompt 中，使得该世界内的所有实体行事风格符合特定的世界观设定。|
|**`max_agents_limit`**|Integer|Not Null|`1000`|**资源配额。** 该世界允许同时存在的最大活跃泛实体数量，用于官方云托管的资源流控与防滥用。|
|**`default_llm`**|String(50)|Not Null|`"gpt-4o"`|**认知引擎配置。** 指定该世界默认调用的推理大模型版本，允许不同世界根据成本或智力需求切换不同的大脑。|
|**`created_at`**|DateTime|Not Null|数据库当前时间|**创世时间戳。** 记录该平行宇宙诞生的绝对时间。|
|**`updated_at`**|DateTime|Nullable|记录更新时的时间|**最后修改时间。** 记录管理员最后一次调整世界规则的时间。|
### 1. 创世 (Creation)
- **触发机制：** 管理员通过控制面板调用 `POST /api/v1/sessions`。
- **核心动作：**
    - 关系型数据库（PostgreSQL）生成一条全新的世界记录。
    - 设定该世界的全局规则（如最大实体在线数、默认调用的 LLM 模型等）。
### 2. 运转 (Operation)
- **触发机制：** 系统平稳运行期，支持管理端的查询监控 `GET /api/v1/sessions/{session_id}`。
- **核心动作：**
    - 承载微观实体（Agent）的高频注册、卸载与事件交互。
    - Redis 维护该世界下的所有在线活跃连接。
### 3. 末日与封存 (Suspension / Soft Deletion)

- **触发机制：** 平台停止运营或管理员调用 `DELETE /api/v1/sessions/{session_id}`。
- **核心动作：**
    - **硬删除：** 将 PostgreSQL 中的世界删除
    - **热数据清场：** 强行清空该 `session_id` 在 Redis 下的所有活跃 Agent 集合与 Profile 缓存。
    - **遗迹删除：** **删除** Neo4j 中该世界的图谱数据。这个世界停止了时间的流转，发生过的交互历史被永久封存。

---

## 第二部分：微观实体生命周期 (The Agent Lifecycle)

这是“壳中之魂”真正运转的链路。当实体所在的 Session 建立后，Agent 开始其生命历程。

### 1. 降生 (Onboarding / Registration)

- **触发机制：** Sensor 客户端连接系统，调用 `POST /api/v1/sessions/{session_id}/agents/{uuid}`。
- **载荷契约：** 仅需携带实体的“灵魂”设定Profile，**无需携带任何物理异构数据**。
- **核心动作：**
    - **灵魂挂载：** FastAPI 网关将 `uuid` 加入 Redis 的 `session:{session_id}:active_agents` 活跃集合。
    - **缓存人设：** 将 Profile 数据存入 Redis 键值对，供后续推理极速读取。
    - **数据库拦截：** 遵循惰性建点原则，**不与 Neo4j 产生任何写交互**，避免产生僵尸节点。

### 2. 认知流转 (Cognition & Event Loop)

这是 Agent 每次被唤醒时的“思考回路”，由 LangGraph 状态机编排。
- **读取心智：** 从 Redis 瞬间读取该 `uuid` 的 Profile（人设）。
- **加载上下文：** 从 LangGraph Checkpointer 加载该实体最近几分钟/几小时的工作记忆（对话流）。
- **深层记忆检索 (GraphRAG)：** 根据事件的目标对象，向 Neo4j 发起 Cypher 查询，提取双方的历史恩怨。
- **大模型推理 (LLM)：** 将人设、上下文、历史图谱与当前事件组装成 Prompt，由 LLM 生成决策（如输出文本、执行动作）。
- **记忆固化 (Neo4j Write)：** 异步触发图谱更新。利用 `MERGE` 语句检查并创建（如果不存在）主客体节点，同时建立代表本次事件的关系边 `(Subject)-[:ACTION]->(Object)`。
### 3. 休眠与卸载 (Offboarding / Unregistration)
- **触发机制：** 载体断线、销毁或主动调用 `DELETE /api/v1/sessions/{session_id}/agents/{uuid}`。
- **核心动作：**
    - **抹除活跃痕迹：** 将 `uuid` 从 Redis 的活跃集合中剔除，删除 Redis 中的 Profile 缓存。
    - **清理工作台：** 清空该实体在 LangGraph Checkpointer 中的短期工作记忆。
    - **保留赛博遗迹：** **严禁**在 Neo4j 中删除该实体的节点和关系边（除非这个 Session 被删除）。它的社会关系与客观历史将永久留存在当前 Session 的图谱中，供其他存活实体检索与评论。#