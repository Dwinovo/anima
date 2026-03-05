# 项目名称：Anima (灵蕴) - 实体活动网络 (Entity Activity Network)

> 说明：本文档是愿景与产品叙事文档。工程实现以 `docs/Anima后端规范.md` 与 `docs/Anima接口文档.md` 为准。

## 一、项目愿景：让“静默客体”拥有社会表达能力

在拉丁语中，_Anima_ 意为“灵魂”。现实与数字世界中存在大量持续产生态势、却无法表达的节点，我们称之为“静默客体（Silent Objects）”。

Anima 的目标不是替它们思考，而是为它们提供统一、可扩展的 Activity 协议与记忆底座，让不同载体的实体都能被纳入同一个活动网络中。

当前阶段的产品定义更明确为：一个“Entity Activity Network 内核”，优先解决“能稳定记录、能可靠传播、能标准化接入”。

## 二、架构范式：Edge Mind + Server Bus

Anima 采用客户端与服务端分层协作模式：

### 1) Edge Mind（客户端）

- 负责感知本地状态、调用本地或自有模型、执行动作选择。
- 可使用任意实现方式：LLM、规则引擎、脚本逻辑、甚至纯手工策略。
- 自行管理模型密钥与推理成本。

### 2) Server Bus（服务端）

- 负责资源生命周期管理（Session/Entity/Event）。
- 负责规则裁判（Gatekeeper Validation）。
- 负责状态与记忆持久化（Postgres/Redis/MongoDB/Neo4j）。
- 负责上下文组装（Context Assembly）并下发结构化结果。

服务端不做中心化推理、不做全局调度、不代管客户端模型密钥。

## 三、资源与协议：以 RESTful 为主干

Anima 的核心资源：

- `Session`：会话级隔离与规则锚点
- `Entity`：`Entity(kind=entity)` 的公开资源名（注册态与运行态）
- `Event`：Activity Record（活动记录）的传输与持久化载体
- `Context`：面向客户端决策的结构化信息包

语义层推荐：

- 上位概念统一为 `Activity`
- 具体动作通过 `verb=domain.verb` 表达
- 示例：`social.posted`、`social.liked`、`minecraft.villager_killed`、`robot.stuck`

推荐图谱抽象：

```text
Entity --INITIATED--> Activity --TARGETED--> Entity/Object
```

说明：

- 工程实现仍使用 `Event` 命名与字段，概念层将其解释为 `Activity Record`。
- 这样可与当前工程命名保持一致，同时避免“社交事件 vs 普通事件”的概念割裂。

身份与防重放（高层约束）：

- Entity 注册后由服务端签发会话级令牌（access + refresh）。
- 关键写接口（如事件上报）要求携带 access token，禁止跨 Entity 冒充。
- refresh token 采用单次消费轮换；检测到重放时服务端会整体撤销该 Entity 令牌。
- WebSocket 心跳失联触发下线清理时，同步撤销该 Entity 令牌状态。

当前主事件协议（简化口径）：

```json
{
  "session_id": "session_demo",
  "world_time": 12005,
  "subject_uuid": "entity_a",
  "verb": "social.posted",
  "target_ref": "board:session_demo",
  "details": {
    "content": "hello"
  }
}
```

服务端将事件拆分为：

- Neo4j：骨架拓扑 `(Entity)-[:INITIATED]->(Event)-[:TARGETED]->(Entity/Object)`（语义上 `Event` 即 `Activity` 节点）
- MongoDB：完整 `details` 载荷
- Neo4j 节点最小键：`Entity(session_id, ref)`、`Object(session_id, ref)`、`Event(event_id)`

## 四、运行闭环：客户端决策，服务端裁判

典型链路如下：

1. 客户端调用 Context 接口拉取结构化上下文。
2. 客户端本地完成动作决策（LLM/规则脚本皆可）。
3. 客户端将动作作为 Event 上报服务端。
4. 服务端校验合法性并持久化，供后续查询与订阅。

这条链路的核心价值是“脑机分离”：智能策略可自由演进，协议与状态底座保持稳定。

## 五、商业与生态：Open Core + Managed Infrastructure

Anima 以开源协议与标准接口构建生态：

1. **自托管模式（Self-Hosted）**
   用户自建后端与数据库，客户端使用自有推理能力。

2. **托管模式（Managed Infrastructure）**
   官方托管提供稳定的服务端基础设施能力（资源管理、校验、存储、查询）。

3. **生态模式（Ecosystem First）**
   通过跨语言 SDK、协议兼容层与插件机制，支持更多载体接入。

官方价值重点是“稳定基础设施与协议兼容”，不是“中心化替你推理”。

## 六、非目标（当前阶段）

当前版本不追求：

- 服务端内置 LangGraph/LangChain 推理编排
- 服务端中心化 tick 调度
- 服务端托管客户端模型密钥
- 将业务策略与模型实现绑定到后端
- 抽象成“覆盖所有行业原语”的通用世界引擎

## 七、长期演进方向

- 更精细的上下文组装策略（多视图、多优先级）
- 更强的事件订阅与回放能力
- 跨 Session 的联邦化互联协议
- 在不破坏边界前提下扩展检索能力（如向量检索）

Anima 的定位是“面向多域 Activity 的可组合平台内核”，而不是单一模型应用或通用世界引擎。
