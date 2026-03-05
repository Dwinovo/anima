from __future__ import annotations

from src.infrastructure.persistence.neo4j.graph_event_repository import Neo4jGraphEventRepository


def test_to_entity_ref_normalizes_supported_formats() -> None:
    """验证实体引用会被标准化为 entity:<id> 形式。"""
    assert Neo4jGraphEventRepository._to_entity_ref("entity_1") == "entity:entity_1"
    assert Neo4jGraphEventRepository._to_entity_ref("entity:entity_1") == "entity:entity_1"
    assert Neo4jGraphEventRepository._to_entity_ref("entity:router_1") == "entity:router_1"


def test_extract_target_entity_ref_from_entity_like_target() -> None:
    """验证实体目标引用会被识别为 Entity 节点引用。"""
    assert Neo4jGraphEventRepository._extract_target_entity_ref("entity:entity_1") == "entity:entity_1"
    assert Neo4jGraphEventRepository._extract_target_entity_ref("entity:router_1") == "entity:router_1"
    assert Neo4jGraphEventRepository._extract_target_entity_ref("entity_plain") == "entity:entity_plain"


def test_extract_target_entity_ref_rejects_object_refs() -> None:
    """验证客体引用会判定为 Object 而非 Entity。"""
    assert Neo4jGraphEventRepository._extract_target_entity_ref("board:session_demo") is None
    assert Neo4jGraphEventRepository._extract_target_entity_ref("event_123") is None
    assert Neo4jGraphEventRepository._extract_target_entity_ref("object:post_1") is None
