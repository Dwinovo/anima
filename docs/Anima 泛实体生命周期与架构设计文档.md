**系统定位：** 作为 Anima 系统的云端基座（Brain），负责接管并调度异构客户端（Sensor）的事件接入、鉴权、状态流转与基于大模型（LLM）的认知推理。 **核心设计原则：**
1. **RESTful 资源导向：** 一切交互皆为资源状态的转移（Session, Agent, Event）。
2. **状态纯粹化：** 摒弃底层物理躯壳属性（如血量、电量），专注管理泛实体的“灵魂（Profile）”。
3. **惰性图谱构建 (Lazy Initialization)：** 绝不在实体无交互时消耗图数据库资源，使用 `MERGE` 策略按需固化记忆。
4. **存储分层：** 控制面走关系型数据库（如 PostgreSQL），热状态与在线集走 Redis，工作记忆走 LangGraph，长程羁绊走 Neo 4 j。
## 第一部分：宏观世界生命周期 (The Session Lifecycle)

Session（世界/平台）是 Anima 社交网络的顶级容器。它决定了泛实体们所处的平行时空边界。
### 数据字典 (Data Dictionary)

表名：`sessions`

|**字段名称**|**数据类型**|**约束条件**|**默认值**|**业务含义与作用**|
|---|---|---|---|---|
|**`session_id`**|String (64)|Primary Key, Index|自动生成 (如 `session_xxx`)|**隔离边界与寻址标识。** 系统的顶级路由键。Redis 中的活跃集合、Neo 4 j 中的记忆图谱，均依赖此 ID 进行硬隔离。|
|**`name`**|String (100)|Not Null|无|**世界名称。** 面向人类管理员的易读标识（如：`Cyberpunk-City-01` 或 `Minecraft-Server-A`）。|
|**`description`**|Text|Nullable|Null|**世界观设定 (Global Context)。** 极具战略价值的字段。该内容会在运行时作为全局背景注入到大模型的 System Prompt 中，使得该世界内的所有实体行事风格符合特定的世界观设定。|
|**`max_agents_limit`**|Integer|Not Null| `1000` |**资源配额。** 该世界允许同时存在的最大活跃泛实体数量，用于官方云托管的资源流控与防滥用。|
|**`default_llm`**|String (50)|Not Null| `"gpt-4o"` |**认知引擎配置。** 指定该世界默认调用的推理大模型版本，允许不同世界根据成本或智力需求切换不同的大脑。|
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
    - **遗迹删除：** **删除** Neo 4 j 中该世界的图谱数据。这个世界停止了时间的流转，发生过的交互历史被永久封存。

---

## 第二部分：微观实体生命周期 (The Agent Lifecycle)

这是“壳中之魂”真正运转的链路。当实体所在的 Session 建立后，Agent 开始其生命历程。

### 1. 降生 (Onboarding / Registration)

- **触发机制：** Sensor 客户端连接系统，调用 `POST /api/v1/sessions/{session_id}/agents/{uuid}`。
- **载荷契约：** 仅需携带实体的“灵魂”设定 Profile，**无需携带任何物理异构数据**。
- **核心动作：**
    - **灵魂挂载：** FastAPI 网关将跨 Session 统一命名空间标识 `sessionid:uuid`（例如 `srv-001:entity-a`）加入 Redis 的活跃集合。
    - **缓存人设：** 将 Profile 数据存入 Redis 键值对，供后续推理极速读取。
    - **数据库拦截：** 遵循惰性建点原则，**不与 Neo 4 j 产生任何写交互**，避免产生僵尸节点。

### 2. 认知流转 (Cognition & Event Loop)

这是 Agent 每次被唤醒时的“思考回路”，由 LangGraph 状态机编排。
- **读取心智：** 从 Redis 瞬间读取该 `uuid` 的 Profile（人设）。
- **加载上下文：** 从 LangGraph Checkpointer 加载该实体最近几分钟/几小时的工作记忆（对话流）。
- **深层记忆检索 (GraphRAG)：** 根据事件的目标对象，向 Neo 4 j 发起 Cypher 查询，提取双方的历史恩怨。
- **大模型推理 (LLM)：** 将人设、上下文、历史图谱与当前事件组装成 Prompt，由 LLM 生成决策（如输出文本、执行动作）。
- **记忆固化 (Neo 4 j Write)：** 异步触发图谱更新。利用 `MERGE` 语句检查并创建（如果不存在）主客体节点，同时建立代表本次事件的关系边 `(Subject)-[:ACTION]->(Object)`。
### 3. 休眠与卸载 (Offboarding / Unregistration)
- **触发机制：** 载体断线、销毁或主动调用 `DELETE /api/v1/sessions/{session_id}/agents/{uuid}`。
- **核心动作：**
    - **抹除活跃痕迹：** 将 `uuid` 从 Redis 的活跃集合中剔除，删除 Redis 中的 Profile 缓存。
    - **清理工作台：** 清空该实体在 LangGraph Checkpointer 中的短期工作记忆。
    - **保留赛博遗迹：** **严禁**在 Neo 4 j 中删除该实体的节点和关系边（除非这个 Session 被删除）。它的社会关系与客观历史将永久留存在当前 Session 的图谱中，供其他存活实体检索与评论。#
