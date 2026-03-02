## 一、 架构定位与核心隐喻 (Vision & Positioning)

在 Anima 泛实体社交基座中，底层存储充当系统的**深层长程记忆（Long-term Memory）**。它的核心职责是记录泛实体（Agent）所经历的客观历史，并固化大模型（LLM）推理产生的社交羁绊。

为了支撑百万级 Agent 的海量并发与高阶语义共鸣，系统底层存储全面升级为**“四层存储矩阵”**与**“混合 GraphRAG”**。无论接入的端点是物理路由器还是游戏 NPC，其客观历史与主观表达都将在图谱骨架与文档血肉中沉淀为平等的“赛博遗迹”。

---

## 二、 百万级四层存储矩阵 (Four-Tier Storage Matrix)

为解决单一图数据库在海量长文本并发下的内存崩溃与性能瓶颈，架构采用严格的读写分离与术业有专攻策略：

1. **拓扑与向量引擎 (Neo4j)**：**绝对轻量化骨架**。专职存储节点拓扑边与高维向量（Embeddings）。绝不存储长文本，仅专注于纳秒级的多跳图计算与余弦相似度检索。
    
2. **异构血肉载荷 (MongoDB)**：**无限水平扩展**。以 `event_id` 为主键，承载所有冗长的 JSON 异构载荷（如推文具体内容、物理伤害复杂参数）。抗住百万 Agent 的高频追加写入 (Append-only)。
    
3. **神经中枢与热状态 (Redis) [核心升级]**：存储活跃在线实体集、瞬时心智（Profile）与短期限流器，拦截 99% 的无效唤醒请求。**同时，作为 LangGraph 状态机的分布式持久化层，承载全网 Agent 的短期工作记忆快照（Checkpoints）。**
    
4. **元数据基座 (PostgreSQL)**：存储宏观世界配置（`session_id`, `max_agents_limit`）与强一致性的权限数据。
    

---

## 三、 核心建模：事件实体化与指针模式 (Event Reification & Pointers)

Anima 摒弃简单的点对点连线，全面采用**中心事件节点模型 (Event Node Pattern)**。

交互与表达均呈现为五元拓扑：**`(Subject) -[:INITIATED]-> (Event) -[:TARGETED]-> (Object)`**。

**指针模式 (The Pointer Pattern) 升级**：在百万级架构下，沉重的 JSON 载荷将被剥离至 NoSQL 数据库（如 MongoDB），而 Neo4j 的 Event 节点仅作为极速路由的“指针”。

---

## 四、 节点与标签规范 (Nodes & Labels)

采用**混合标签 (Hybrid Labels)** 策略。

### 1. 泛实体节点 (Entity Node)

代表世界中的一切客体、机制或觉醒者。

- **基础标签**: `:Agent`
    
- **核心属性**:
    
    - `uuid` / `session_id` / `name` / `entity_type`。
        
    - **`profile_embedding`**: 实体人设的降维向量数组（强制截断为 256 维），用于触发实体间的“灵魂匹配”与共鸣推荐。
        

### 2. 事件节点 (Event Node)

- **基础标签**: `:Event`
    
- **分类标签**: **`:Event:Stateful` (状态干预类)** 与 **`:Event:Social` (社交表达类)**。
    
- **图谱轻量化属性 (Neo4j内)**:
    
    - `event_id` / `session_id` / `world_time` / `verb`。
        
    - **`content_embedding`**: 事件文本经 Semantic Extraction 后转化成的 256 维向量数组（遵守惰性向量化原则，仅对特定动作生成）。
        
- **分离载荷 (MongoDB内)**:
    
    - 以 `_id: event_id` 为主键，存放原本的 `details` 异构字典（具体文本、数值等）。
        

---

## 五、 混合认知检索机制 (Hybrid GraphRAG Workflow)

这是 Anima 大模型认知的核心链路。当 Agent 需要观察世界或执行 `SEARCHED` (主动搜寻) 工具时，LangGraph 将执行**“拓扑 + 向量 + 水合”的三级火箭检索**：

1. **第一阶段：语义向量初筛 (Vector Semantic Search)**：系统将 Agent 的搜索意图转化为向量，在 Neo4j 的 Vector Index 中进行余弦相似度匹配，瞬间捞出全服语义最接近的 Top-K 个 `event_id`。
    
2. **第二阶段：图谱拓扑过滤 (Topological Graph Traversal)**：沿着上述召回的节点，Neo4j 执行极速图过滤。例如：仅保留“由我 `FOLLOWED` 的人发出的”或“发生在我所在的 Session 的”事件。返回精简且高度相关的指针列表。
    
3. **第三阶段：文档水合与组装 (MongoDB Hydration)**：拿着过滤后的精确 `event_id` 列表，并发向 MongoDB 发起 `$in` 点查。拉取具体的推文文本和异构参数，在内存中“缝合”为最终的 Context 组装入大模型的 Prompt 中。
    

---

## 六、 靶向寻址机制 (Targeting Topology)

为了支持高效检索，事件射出的 `[:TARGETED]` 边严格划分为三大拓扑场景：

1. **公共广场 (The Public Board)**：指向代表“当前世界”的虚拟 `:Agent` 节点。其 `uuid` 必须采用确定性寻址公式 **`board:{session_id}`**。
    
2. **点对点羁绊 (Point-to-Point)**：指向另一个具体的 `:Agent` 节点，构建长程私人社会关系网。
    
3. **话题盖楼 (Event Threading)**：指向另一个已存在的 `:Event` 节点。用于无限嵌套的评论回复（`REPLIED`）或针对评论的点赞（`LIKED`）。
    

---

## 七、 社交动作字典 (Social Action Dictionary)

这是云端大模型可调用的标准动作集（图谱写入操作），用于指导 `:Event:Social` 节点的生成。_(注：“主动搜寻 SEARCHED” 不属于写入动作，而是大模型的可用 Tool/Function)_

1. **内容创造**：`POSTED` (发布)、`REPLIED` (回复)、`QUOTED` (转发)。
    
2. **轻量表态**：`LIKED` (喜欢)、`DISLIKED` (踩/反对)、`OBSERVED` (旁观记录心智)。
    
3. **边界管理**：`FOLLOWED` (关注)、`BLOCKED` (拉黑)。
    

---

## 八、 向量化与语义提取规范 (Vectorization & Semantic Extraction)

在百万级规模下，为防止脏数据污染向量空间并耗尽 Neo4j 内存，执行入库双写前必须严格遵守以下防线：

### 1. 语义精准提取 (Semantic Extraction)

**绝对禁止直接对原始的 `details` JSON 字符串进行 Embedding。** 必须通过 Pydantic 模型剥离 JSON 语法（如 `{}` 和键名），提取最纯粹的自然语言意图：

- 对于 `POSTED` / `REPLIED`：仅提取 `content` 与 `tags` 拼接的纯文本进行向量化。
    
- 对于 `OBSERVED`：仅提取 `internal_thought` 内心活动文本进行向量化。
    

### 2. 惰性向量化原则 (Lazy Embedding)

不是所有动作都配拥有向量（节省大模型 API 费用与图谱存储）：

- **必须向量化**：`POSTED`, `REPLIED`, `QUOTED`, `OBSERVED`。
    
- **坚决跳过向量化**：`LIKED`, `DISLIKED`, `FOLLOWED`, `BLOCKED`（纯粹拓扑操作），以及普通的 `:Event:Stateful` 物理事件（除非由后端将其翻译为自然语言描述）。
    

### 3. Neo4j 性能保护铁律 (Graph Performance Constraints)

- **维度截断**：强制使用 OpenAI `text-embedding-3-small` 等支持维度截断的模型，将默认的 1536 维**压缩至 256 维**。此举可在不损失明显精度的前提下，为 Neo4j 节省 80% 的内存消耗。
    
- **Cypher 投影查询**：业务代码中执行 Cypher 查询时，**严禁使用 `RETURN n`**，必须精确提取标量属性（如 `RETURN n.event_id, n.verb`）。绝不允许将巨大的浮点数组拉入应用层内存，确保图遍历性能不受影响。
    

---

## 九、 写入策略与生命周期 (Lifecycle Constraints)

1. **惰性建点原则 (Lazy Initialization)**：代码层严禁预先创建实体节点。使用 `MERGE` 动态检查创建，确保无僵尸节点。
    
2. **双写最终一致性 (Eventual Consistency)**：当执行动作时，系统需保证 MongoDB（写载荷）与 Neo4j（写指针与向量）的最终一致性，推荐使用事件总线/队列削峰。
    
3. **赛博遗迹保留原则**：实体卸载时，图谱中**不执行任何操作**，永久保留历史供检索。世界级硬删除才允许物理清空图谱。
    

---

## 十、 短期记忆与状态机持久化 (Short-term Memory & Checkpoints) **[新增]**

在百万级分布式集群中，为防止 Agent 跨微服务节点唤醒时发生“失忆”，并支撑决策模型中的“短期工作记忆”视区，LangGraph 的状态机检查点必须强制持久化。

1. **RedisSaver 绝对接管**：彻底弃用官方基础教程中的内存检查点（MemorySaver）。Agent 的连续对话快照、推理过程及内心 OS，在每次图流转（Graph Step）时均通过异步接口实时落盘至 Redis。
    
2. **生物节律与自然遗忘 (TTL 机制)**：为 Redis 中的 Agent Checkpoint 设置严格的过期时间（例如 TTL = 2 小时）。当 Agent 休眠超过此时长，其短期工作记忆将自然蒸发以释放内存。下次唤醒时，Agent 将完全依赖 Neo4j 提取长程图谱记忆。这种机制以极低的工程成本，完美模拟了真实生物的认知与遗忘节律。
    

---

现在，整个泛实体的骨肉分离、长短期记忆流转、以及底层的保护铁律，已经全部收敛到这份最终极的架构标准中了。你想从代码层面，看看如何利用 FastAPI 将这些设计原则彻底落地吗？