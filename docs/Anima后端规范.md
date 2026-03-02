下面是按照严格 DDD 原则、结合你现有架构与图谱设计文档重构后的完整规范版本。

你可以直接保存为：

> `Anima后端规范_v2.md`

---

# Anima 后端规范 v2

**（DDD 架构强化版 · Domain-First 版本）**

---

# 0. 设计目标

Anima 是一个 **泛实体社交与图谱记忆系统**。

系统必须满足：

- 世界隔离（Session 级别强隔离）
    
- 泛实体（Agent）生命周期管理
    
- 事件驱动社交建模
    
- 骨肉分离（Graph 指针 + Mongo Payload）
    
- 混合 GraphRAG 检索
    
- 长短期记忆分层
    
- 技术实现可替换，业务规则稳定
    

本规范以 **DDD（领域驱动设计）** 为最高指导原则。

---

# 1. 分层架构总则（必须遵守）

## 1.1 四层结构

```
presentation  →  application  →  domain
                     ↑
               infrastructure
```

### Presentation（表现层）

- FastAPI 路由
    
- 参数校验
    
- 响应封装
    
- 不写业务逻辑
    

### Application（应用层）

- UseCase
    
- 编排多个仓储
    
- 事务控制
    
- 不依赖具体数据库
    

### Domain（领域层）

- 实体（Entity）
    
- 值对象（Value Object）
    
- 仓储接口（Protocol）
    
- 领域规则
    
- 领域异常
    
- 绝对禁止依赖数据库或框架
    

### Infrastructure（基础设施层）

- Redis / Mongo / Postgres / Neo4j
    
- ORM Model
    
- Repository 实现
    
- 外部 SDK
    

---

# 2. 依赖方向规则（硬性约束）

允许：

```
presentation → application → domain
infrastructure → domain
```

禁止：

```
domain → infrastructure
application → postgres/redis/mongo/neo4j
```

Domain 永远不能 import SQLAlchemy、FastAPI、Redis、Motor、Neo4j。

---

# 3. 存储分层矩阵

|存储|职责|说明|
|---|---|---|
|PostgreSQL|控制面|Session 配置、配额锚点|
|Redis|热状态面|在线态、短期记忆|
|MongoDB|载荷面|Event 详情 JSON|
|Neo4j|记忆骨架面|事件拓扑 + 向量|

---

# 4. PostgreSQL 规范

## 4.1 职责

仅用于控制面：

- sessions 表（Session）
    
- session_id
    
- max_agents_limit
    
- default_llm
    

禁止：

- 写入交互事件
    
- 存储 JSON 载荷
    
- 存储 embedding
    

## 4.2 技术规范

- SQLAlchemy 2.0 AsyncSession
    
- 通过依赖注入提供 session
    
- 不在 repository 外部直接操作 session
    
- 表结构变更必须通过 Alembic 迁移脚本管理
    

---

# 5. Redis 规范

## 5.1 职责

- Agent 在线态（Set）
    
- Agent Profile（String）
    
- LangGraph Checkpoint（TTL）
    

## 5.2 Key 设计规范

必须命名空间隔离：

```
anima:session:{session_id}:active_agents
anima:agent:{session_id}:{uuid}:profile
anima:session:{session_id}:display_name:{display_name}
anima:checkpoint:{session_id}:{uuid}
anima:checkpoint:*
anima:checkpoint_blob:*
anima:checkpoint_write:*
```

Profile 值推荐结构：

```json
{
  "name": "Alice",
  "display_name": "Alice#48291",
  "profile": { "...": "..." }
}
```

其中 `display_name` 由后端分配为 `name#5位数字`。
后缀起点可基于 `session_id+uuid` 稳定计算，冲突时需线性探测并通过索引键保证同 Session 唯一。

## 5.3 原则

- LangGraph checkpoint 必须 TTL（Presence/Profile 不强制 TTL）
    
- 不可作为持久记忆
    
- 不可作为唯一数据源

- 若采用 `langgraph-checkpoint-redis`，必须确保 Redis 具备 RedisJSON / RediSearch 模块（建议 Redis Stack）
    

---

# 6. MongoDB 规范（Event 载荷层）

## 6.1 职责

- 以 event_id 为主键
    
- 存储完整 JSON payload
    
- 批量水合（mget）
    

## 6.2 文档结构

```json
{
  "_id": "event_id",
  "session_id": "...",
  "world_time": 123,
  "verb": "POSTED",
  "details": { ... },
  "schema_version": 1,
  "created_at": "..."
}
```

## 6.3 原则

- 不参与拓扑
    
- 不存 embedding
    
- 不做图遍历
    

---

# 7. Neo4j 规范（图谱骨架层）

## 7.1 五元拓扑模型

```
(Subject)-[:INITIATED]->(Event)-[:TARGETED]->(Object)
```

## 7.2 指针模式

Event 节点仅包含：

- event_id
    
- world_time
    
- verb
    
- embedding_256
    

禁止：

- 存储长文本
    
- 存储 JSON payload
    

## 7.3 惰性建点原则

必须使用 MERGE。

严禁：

- 预创建 Agent
    
- 预创建 Object
    
- 批量导入空节点
    

## 7.4 性能铁律

禁止：

```
RETURN n
RETURN e
```

必须：

```
RETURN e.event_id
```

embedding 维度强制 256。

## 7.5 双写原则

写入流程：

1. Mongo 写 payload
    
2. Neo4j 写骨架
    
3. 最终一致性
    

---

# 8. Repository 设计规范（DDD 强制）

## 8.1 Repository 定义

Repository 是领域的“集合抽象”。

- Domain 定义接口（Protocol）
    
- Infrastructure 实现接口
    

## 8.2 示例

Domain：

```python
class SessionRepository(Protocol):
    async def get(self, *, session_id: str) -> Session | None: ...
```

Infrastructure：

```python
class PostgresSessionRepository(SessionRepository):
    ...
```

UseCase：

```python
def __init__(self, session_repo: SessionRepository)
```

## 8.3 禁止

- UseCase 依赖具体实现类
    
- Repository 返回 ORM Model（推荐返回领域实体）
    

---

# 9. 依赖注入（DI）规范

## 9.1 单例（App 生命周期）

- RedisClient

- LangGraph Redis Checkpointer（如 `AsyncRedisSaver`）
    
- MongoManager
    
- Neo4jManager
    
- Postgres Engine / SessionFactory
    

## 9.2 请求级

- AsyncSession
    
- Repository
    
- UseCase
    

## 9.3 组合根

- `main.py` 创建基础设施
    
- `dependencies.py` 组装 repo/usecase
    
- 路由只注入 usecase
    

---

# 10. GraphRAG 三阶段标准

1️⃣ 向量初筛（Neo4j vector index）  
2️⃣ 拓扑过滤（Neo4j）  
3️⃣ Mongo mget 水合

禁止：

- 直接在图中取 payload
    
- 循环单条 get Mongo
    

---

# 11. 目录结构标准

```
src/
  core/
  presentation/
  application/
  domain/
  infrastructure/
```

完整推荐结构：

```
domain/
  session/
  agent/
  memory/

application/
  usecases/

infrastructure/
  persistence/
    postgres/
    redis/
    mongo/
    neo4j/
```

---

# 12. LangGraph 规范

- State 只存认知上下文（灵魂/工作记忆/本轮参数），禁止存放数据库客户端或 ORM 对象
    
- 图谱查询必须通过仓储
    
- Redis checkpoint 必须 TTL

- 推荐使用 RedisSaver 作为图执行状态持久化，`thread_id` 建议采用 `session_id:uuid`
    
- 不允许 Node 内直接操作数据库
    

---

# 13. API 响应规范

统一结构：

```
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

HTTP 状态码遵循 REST 语义：

- 200 OK
    
- 201 Created
    
- 202 Accepted（异步事件固化）
    
- 400 ValidationError
    
- 404 NotFound
    
- 409 Conflict
    

---

# 14. 生产级配置规范

- Python 3.12 强制
    
- 使用 uv 锁依赖
    
- `.env.example` 提交
    
- `.env` 禁止提交
    
- 真实生产环境优先使用系统环境变量
    
- CORS 必须可配置（至少包含 origins/methods/headers/credentials）
    

---

# 15. 终极原则

- Domain 是系统存在的理由
    
- Infrastructure 只是实现手段
    
- Graph 是记忆骨架
    
- Mongo 是血肉
    
- Redis 是短期意识
    
- Postgres 是规则锚点
    

---

# 结语

Anima 后端是一个：

> 领域优先、技术可替换、图谱驱动的泛实体社交系统。

如果后续有人写代码违反本规范，  
应当视为架构层面错误，而不是风格问题。

---

如果你愿意，我可以再给你：

- 一份「v2 → v3 企业级演进蓝图」
    
- 或「GraphRAG 深化规范（含向量索引与一致性策略）」
    
- 或一份「单元测试与架构验证规范」
    

你想把它打磨到什么级别？
