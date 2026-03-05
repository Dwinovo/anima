from __future__ import annotations

from src.infrastructure.persistence.neo4j.cypher import NEO4J_SCHEMA_STATEMENTS


def test_neo4j_schema_statements_cover_core_constraints_and_indexes() -> None:
    """验证 Neo4j 预置语句覆盖三节点唯一约束与核心索引。"""
    joined = "\n".join(NEO4J_SCHEMA_STATEMENTS)

    assert "CONSTRAINT entity_ref_unique IF NOT EXISTS" in joined
    assert "CONSTRAINT object_ref_unique IF NOT EXISTS" in joined
    assert "CONSTRAINT event_event_id_unique IF NOT EXISTS" in joined
    assert "INDEX event_session_world_time IF NOT EXISTS" in joined
    assert "INDEX event_verb IF NOT EXISTS" in joined
