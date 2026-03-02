from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AgentLifecycleResult:
    """Agent 生命周期操作结果 DTO。"""

    session_id: str
    uuid: str
    active: bool
    name: str | None = None
    display_name: str | None = None


__all__ = ["AgentLifecycleResult"]
