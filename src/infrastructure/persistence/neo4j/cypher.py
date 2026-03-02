from __future__ import annotations

UPSERT_EVENT = """
MERGE (s:Agent {session_id: $session_id, uuid: $subject_uuid})
MERGE (o:Object {session_id: $session_id, ref: $target_ref})
MERGE (e:Event {session_id: $session_id, event_id: $event_id})
SET
  e.world_time = $world_time,
  e.verb = $verb,
  e.embedding_256 = $embedding_256
MERGE (s)-[:INITIATED]->(e)
MERGE (e)-[:TARGETED]->(o)
"""

RECENT_EVENT_IDS = """
MATCH (e:Event {session_id: $session_id})
RETURN e.event_id AS event_id
ORDER BY e.world_time DESC
LIMIT $limit
"""

TOPOLOGY_FILTER = """
MATCH (a:Agent {session_id: $session_id, uuid: $anchor_uuid})
      -[:INITIATED]->(e:Event)
WHERE e.session_id = $session_id
  AND e.event_id IN $event_ids
RETURN e.event_id AS event_id
ORDER BY e.world_time DESC
LIMIT $limit
"""
