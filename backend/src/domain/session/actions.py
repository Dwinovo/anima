from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(slots=True, frozen=True)
class SessionAction:
    """Session 级动作约束。"""

    verb: str
    details_schema: dict[str, Any]
    description: str | None = None


def session_actions_from_payload(
    actions: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...] | None,
) -> tuple[SessionAction, ...]:
    """将序列化 payload 转为领域动作对象。"""
    if not actions:
        return ()

    results: list[SessionAction] = []
    for action in actions:
        details_schema = action.get("details_schema", {})
        results.append(
            SessionAction(
                verb=str(action.get("verb", "")),
                description=action.get("description")
                if isinstance(action.get("description"), str) or action.get("description") is None
                else str(action.get("description")),
                details_schema=dict(details_schema) if isinstance(details_schema, dict) else {},
            )
        )
    return tuple(results)


def session_actions_to_payload(actions: tuple[SessionAction, ...] | list[SessionAction]) -> list[dict[str, Any]]:
    """将领域动作对象转回可序列化结构。"""
    return [
        {
            "verb": action.verb,
            "description": action.description,
            "details_schema": dict(action.details_schema),
        }
        for action in actions
    ]
