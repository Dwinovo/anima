from __future__ import annotations

UPSERT_EVENT_TARGET_ENTITY = """
MERGE (s:Entity {session_id: $session_id, ref: $subject_ref})
MERGE (t:Entity {session_id: $session_id, ref: $target_entity_ref})
MERGE (e:Event {session_id: $session_id, event_id: $event_id})
SET
  e.world_time = $world_time,
  e.verb = $verb
MERGE (s)-[:INITIATED]->(e)
MERGE (e)-[:TARGETED]->(t)
"""

UPSERT_EVENT_TARGET_OBJECT = """
MERGE (s:Entity {session_id: $session_id, ref: $subject_ref})
MERGE (o:Object {session_id: $session_id, ref: $target_ref})
MERGE (e:Event {session_id: $session_id, event_id: $event_id})
SET
  e.world_time = $world_time,
  e.verb = $verb
MERGE (s)-[:INITIATED]->(e)
MERGE (e)-[:TARGETED]->(o)
"""

RECENT_EVENT_IDS = """
MATCH (e:Event {session_id: $session_id})
WHERE
  $before_world_time IS NULL
  OR e.world_time < $before_world_time
  OR (e.world_time = $before_world_time AND e.event_id < $before_event_id)
RETURN e.event_id AS event_id
ORDER BY e.world_time DESC, e.event_id DESC
LIMIT $limit
"""

NEO4J_SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
CREATE CONSTRAINT entity_ref_unique IF NOT EXISTS
FOR (e:Entity) REQUIRE (e.session_id, e.ref) IS UNIQUE
""".strip(),
    """
CREATE CONSTRAINT object_ref_unique IF NOT EXISTS
FOR (o:Object) REQUIRE (o.session_id, o.ref) IS UNIQUE
""".strip(),
    """
CREATE CONSTRAINT event_event_id_unique IF NOT EXISTS
FOR (ev:Event) REQUIRE ev.event_id IS UNIQUE
""".strip(),
    """
CREATE INDEX event_session_world_time IF NOT EXISTS
FOR (ev:Event) ON (ev.session_id, ev.world_time)
""".strip(),
    """
CREATE INDEX event_verb IF NOT EXISTS
FOR (ev:Event) ON (ev.verb)
""".strip(),
)
