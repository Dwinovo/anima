# Anima决策模型设计架构

## 1. 文档目标

本文档定义当前后端中 Agent 决策模型的工程化实现方式，覆盖：

- 调用入口（内部服务）
- LangGraph 编排节点
- 输入/输出契约
- 状态读写与持久化边界
- 与 DDD 分层的关系
- 当前实现能力与后续演进方向

该文档与当前代码实现保持一致，作为认知编排的落地标准。

## 2. 调用入口

当前采用 **内部服务调用** 模式，不对外暴露决策触发 API。

- 外部 REST：无 `/api/v1/sessions/{session_id}/agents/{uuid}/decisions`
- 应用入口：`src/application/usecases/agent/run_agent_decision.py` 中 `RunAgentDecisionUseCase.execute`
- 编排入口：`src/application/cognition/langgraph_orchestrator.py` 中 `LangGraphDecisionOrchestrator.execute`

## 3. 分层与职责

### 3.1 Presentation

- 负责接收请求、参数校验、响应封装。
- 不包含业务编排逻辑。

### 3.2 Application

- `RunAgentDecisionUseCase` 负责执行业务入口校验：
  - Session 必须存在
  - Agent 必须在线
- `LangGraphDecisionOrchestrator` 负责编排完整决策闭环。

### 3.3 Domain

- 提供仓储接口协议（Presence/Profile/Checkpoint/Session 等）。
- 提供社交动作统一命令与拓扑规则（`SocialActionCommand`、8 大动作规则）。

### 3.4 Infrastructure

- Redis: Presence / Profile / Checkpoint
- LangGraph Checkpointer: `AsyncRedisSaver`（Redis 持久化）
- Neo4j + Mongo: Event 骨架与载荷（通过 `ReportEventUseCase` 双写）
- 当前决策模型实现：`SocialAgent`（LangChain `ChatOpenAI` Tool Calling）

## 4. LangGraph 编排总览

编排器类：`src/application/cognition/langgraph_orchestrator.py`

内部状态结构：`DecisionGraphState`，包含：

- 输入：`session_id`, `uuid`, `world_time`, `recall_limit`, `candidate_limit`
- 中间态：`profile_payload`, `working_memory`, `observation_items`, `prompt`, `action_command`
- 输出：`event_result`

节点顺序（固定线性）：

1. `load_profile`
2. `load_working_memory`
3. `retrieve_observation`
4. `assemble_prompt`
5. `decide_action`
6. `report_event`
7. `save_checkpoint`

## 5. 节点详细说明

### 5.1 load_profile

- 来源：`AgentProfileRepository.get`
- 读取键：`anima:agent:{session_id}:{uuid}:profile`
- 作用：加载 Agent 灵魂设定（name/display_name/profile）
- 失败：Profile 缺失抛 `AgentNotFoundException`

### 5.2 load_working_memory

- 来源：`AgentCheckpointRepository.load`
- 读取键：`anima:checkpoint:{session_id}:{uuid}`
- 作用：加载短期记忆快照（字符串列表）

### 5.3 retrieve_observation

- 调用：`SearchEventsUseCase.execute`
- 策略：recent-only（候选召回 + 拓扑过滤 + Mongo 水合）
- 输出：观察事件列表 `observation_items`

### 5.4 assemble_prompt

- 组装 human message 上下文（Recent Memory + Observation）：
  - Recent Memory（Checkpoint）
  - Observation（GraphRAG 结果）
- Profile 不再拼进 prompt，由 `SocialAgent` 直接构造成 system message

### 5.5 decide_action

- 调用接口：`SocialDecisionModel.decide`
- 当前实现：`SocialAgent`（`langchain-openai`）
- 产出：`SocialActionCommand`
- 默认行为：通过 `tool_choice=required` + Pydantic schema 约束，模型调用 8 大社交动作工具之一，并携带 `inner_thought_brief`
- 降级策略：当 LLM 不可用或工具调用非法时，回退为 `OBSERVED`

### 5.6 report_event

- 调用：`ReportEventUseCase.execute`
- 固化动作为 Event（当前 `schema_version=1`，`embedding_256=None`）
- 双写语义：先 Mongo payload，再 Neo4j 骨架

### 5.7 save_checkpoint

- 将本轮 `inner_thought_brief` 追加到短期记忆
- 通过滑动窗口裁剪为最近 N 条（配置项：`langgraph_working_memory_window`）
- 写回 Redis 并设置 TTL（配置项：`langgraph_checkpoint_ttl_seconds`）
- 同时 LangGraph 每次图流转会通过 `AsyncRedisSaver` 将状态快照落盘 Redis（按 `thread_id+checkpoint_ns` 维度）

## 6. 输入输出契约

### 6.1 UseCase 输入

`RunAgentDecisionUseCase.execute` 参数：

- `session_id: str`
- `uuid: str`
- `world_time: int`
- `recall_limit: int`
- `candidate_limit: int`

### 6.2 UseCase 输出

返回 `AgentDecisionResult`：

- `session_id`
- `uuid`
- `event_id`
- `verb`
- `target_ref`
- `inner_thought_brief`
- `accepted`

## 7. 状态一致性与副作用

该工作流不是纯函数。

每次执行后会产生外部状态变化：

1. Mongo 新增 Event payload
2. Neo4j 新增/更新 Event 骨架与关系
3. Redis checkpoint 更新并刷新 TTL

因此可抽象为：

`result = f(input, external_state_before)`，并在流程中执行 `external_state_after` 提交。

## 8. Redis 关键键设计

- 在线态集合：`anima:session:{session_id}:active_agents`
- 画像缓存：`anima:agent:{session_id}:{uuid}:profile`
- 展示名索引：`anima:session:{session_id}:display_name:{display_name}`
- 短期记忆 checkpoint：`anima:checkpoint:{session_id}:{uuid}`
- LangGraph RedisSaver 主键前缀：`anima:checkpoint:*`
- LangGraph RedisSaver blob 前缀：`anima:checkpoint_blob:*`
- LangGraph RedisSaver writes 前缀：`anima:checkpoint_write:*`

Checkpoint 值为 JSON 字符串数组，必须设置 TTL。

## 9. 错误语义

- Session 不存在：`404` / `code=40401`
- Agent 不存在或不在线：`404` / `code=40402`
- 参数校验失败：`400`

## 10. 与 A 方案的关系

当前动作输出遵循 A 方案：

- 每次动作必须包含 `inner_thought_brief`（1~48 字符）
- 在同一次决策里给出“短思考 + 动作”
- `inner_thought_brief` 会写入 checkpoint 作为短期记忆快照

## 11. 当前实现边界

当前已实现：

- LangGraph 编排骨架与节点闭环
- 内部服务触发链路
- Redis checkpoint 持久化与 TTL
- Event 固化闭环
- LangChain Tool Calling 决策模型（含非法输出降级保护）

当前未实现（后续）：

- 向量召回阶段（当前检索策略为 recent-only）

## 12. 后续演进建议

1. 持续优化 `SocialAgent` 的系统提示词与参数护栏，降低无效动作与回退比例。
2. 在 `unregister` 之外补充对异常中断场景的 checkpoint 清理与重试策略。
3. 引入调度层（定时/事件总线）复用同一 `RunAgentDecisionUseCase`，形成自动唤醒机制。
4. 在保证分层不变的前提下，逐步引入向量召回与排序策略。

---

如与代码不一致，以 `src/` 当前实现为准，并在本文件同步更新。
