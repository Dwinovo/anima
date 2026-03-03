from __future__ import annotations

UPSERT_EVENT = """
MERGE (s:Agent {session_id: $session_id, uuid: $subject_uuid})
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
