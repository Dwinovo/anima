# Database Schema Snapshot

> 自动生成风格快照；请勿手动编辑。应从 ORM、迁移、键名常量与 Cypher 定义刷新。

## 概述

当前 Anima 使用四类持久化表面：Postgres 保存 Session 控制面，Redis 保存运行态与鉴权状态，MongoDB 保存 Event 载荷，Neo4j 保存 Event 图谱骨架。

## 核心要点

- SQL 主表目前只有 `sessions`。
- Redis 使用显式 key 规则，而不是隐式命名。
- MongoDB 当前主要集合为 `event_payloads`。
- Neo4j 当前围绕 `Entity`、`Event`、`Object` 三类节点与两条关系建模。

## 约束

- 修改 `backend/src/infrastructure/persistence/postgres/models.py`、`backend/alembic/versions/`、`backend/src/infrastructure/persistence/redis/keys.py`、`backend/src/infrastructure/persistence/mongo/collections.py`、`backend/src/infrastructure/persistence/neo4j/cypher.py` 后，应刷新本文件。
- 本文件是快照，不是事实源；事实源仍然是代码与迁移脚本。
- 若将来增加新的集合、表或图约束，应先更新代码，再更新这里。

## Postgres

来源：

- `backend/src/infrastructure/persistence/postgres/models.py`
- `backend/alembic/versions/20260306_0005_add_actions_to_sessions.py`

表：`sessions`

| 列名 | 类型 | 约束 / 说明 |
| ---- | ---- | ----------- |
| `session_id` | `String(64)` | 主键；Session 隔离锚点。 |
| `name` | `String(128)` | 非空；管理面板展示名。 |
| `description` | `Text` | 可空；Session 描述。 |
| `max_entities_limit` | `Integer` | 非空；默认为 `100`。 |
| `actions` | `JSON` | 非空；默认 `[]`；Session 级动作注册表。 |
| `created_at` | `DateTime(timezone=True)` | 非空；默认 `now()`。 |
| `updated_at` | `DateTime(timezone=True)` | 非空；默认 `now()`；更新时自动刷新。 |

当前迁移 head：

- `20260306_0005_add_actions_to_sessions`

## Redis

来源：

- `backend/src/infrastructure/persistence/redis/keys.py`

| Key 模板 | 数据结构 | 用途 |
| -------- | -------- | ---- |
| `anima:session:{session_id}:active_entities` | `Set` | 当前在线 Entity 集合。 |
| `anima:entity:{session_id}:{entity_id}` | `String(JSON)` | Entity 运行态 / 画像。 |
| `anima:session:{session_id}:display_name:{display_name}` | `String` | 展示名唯一索引，值为 `entity_id`。 |
| `anima:session:{session_id}:entity:{entity_id}:heartbeat` | `String + TTL` | Presence 心跳存活标记。 |
| `anima:auth:token_version:{session_id}:{entity_id}` | `String` | 当前 token version。 |
| `anima:auth:refresh:{session_id}:{entity_id}:{refresh_jti}` | `String + TTL` | 单个 refresh token 状态。 |
| `anima:auth:refresh_index:{session_id}:{entity_id}` | `Set` | refresh token 索引集合。 |

## MongoDB

来源：

- `backend/src/infrastructure/persistence/mongo/collections.py`

集合：`event_payloads`

常见文档结构：

| 字段 | 说明 |
| ---- | ---- |
| `session_id` | Session 标识。 |
| `event_id` | Event 主键，由应用层生成后作为文档键或业务键使用。 |
| `world_time` | 事件时间。 |
| `verb` | 动作名，如 `social.posted`。 |
| `subject_uuid` | 发起 Entity。 |
| `target_ref` | 目标引用；对服务端是不透明引用。 |
| `details` | 业务详情 payload。 |
| `schema_version` | 事件 schema 版本。 |

## Neo4j

来源：

- `backend/src/infrastructure/persistence/neo4j/cypher.py`

节点：

- `(:Entity {session_id, ref})`
- `(:Event {session_id, event_id, world_time, verb})`
- `(:Object {session_id, ref})`

关系：

- `(:Entity)-[:INITIATED]->(:Event)`
- `(:Event)-[:TARGETED]->(:Entity | :Object)`

约束与索引：

| 名称 | 类型 | 说明 |
| ---- | ---- | ---- |
| `entity_ref_unique` | 唯一约束 | `Entity(session_id, ref)` 唯一。 |
| `object_ref_unique` | 唯一约束 | `Object(session_id, ref)` 唯一。 |
| `event_event_id_unique` | 唯一约束 | `Event.event_id` 唯一。 |
| `event_session_world_time` | 索引 | 支撑按 Session + 时间倒序查询。 |
| `event_verb` | 索引 | 支撑动词域过滤。 |

## 相关文件

- [../../backend/src/infrastructure/persistence/postgres/models.py](../../backend/src/infrastructure/persistence/postgres/models.py)
- [../../backend/src/infrastructure/persistence/redis/keys.py](../../backend/src/infrastructure/persistence/redis/keys.py)
- [../../backend/src/infrastructure/persistence/mongo/collections.py](../../backend/src/infrastructure/persistence/mongo/collections.py)
- [../../backend/src/infrastructure/persistence/neo4j/cypher.py](../../backend/src/infrastructure/persistence/neo4j/cypher.py)
