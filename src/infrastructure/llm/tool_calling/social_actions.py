from __future__ import annotations

from typing import Any, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.domain.agent.social_actions import (
    SOCIAL_ACTION_TARGET_RULES,
    SocialActionCommand,
    SocialActionVerb,
    build_board_ref,
    is_target_allowed_for_verb,
)


class InvalidSocialActionToolCallError(ValueError):
    """社交动作工具调用解析失败。"""


class _BaseToolArgs(BaseModel):
    """Tool Calling 参数基类。"""

    inner_thought_brief: str = Field(
        ...,
        min_length=1,
        max_length=48,
        description="极简内心摘要，建议 8-24 字，一句话。",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class _PostedArgs(_BaseToolArgs):
    """POSTED 参数。"""

    content: str = Field(..., min_length=1, max_length=4096)
    tags: list[str] = Field(default_factory=list, max_length=32)


class _TargetRefArgs(_BaseToolArgs):
    """含 target_ref 的参数基类。"""

    target_ref: str = Field(..., min_length=1, max_length=128)


class _RepliedArgs(_TargetRefArgs):
    """REPLIED 参数。"""

    content: str = Field(..., min_length=1, max_length=4096)


class _QuotedArgs(_TargetRefArgs):
    """QUOTED 参数。"""

    content: str = Field(..., min_length=1, max_length=4096)


class _LikedArgs(_TargetRefArgs):
    """LIKED 参数。"""


class _DislikedArgs(_TargetRefArgs):
    """DISLIKED 参数。"""


class _ObservedArgs(_TargetRefArgs):
    """OBSERVED 参数。"""

    internal_thought: str = Field(..., min_length=1, max_length=4096)


class _FollowedArgs(_TargetRefArgs):
    """FOLLOWED 参数。"""


class _BlockedArgs(_TargetRefArgs):
    """BLOCKED 参数。"""


_TOOL_ARGS_MODELS: Final[dict[str, type[_BaseToolArgs]]] = {
    "social_posted": _PostedArgs,
    "social_replied": _RepliedArgs,
    "social_quoted": _QuotedArgs,
    "social_liked": _LikedArgs,
    "social_disliked": _DislikedArgs,
    "social_observed": _ObservedArgs,
    "social_followed": _FollowedArgs,
    "social_blocked": _BlockedArgs,
}

_TOOL_VERB_MAP: Final[dict[str, SocialActionVerb]] = {
    "social_posted": SocialActionVerb.POSTED,
    "social_replied": SocialActionVerb.REPLIED,
    "social_quoted": SocialActionVerb.QUOTED,
    "social_liked": SocialActionVerb.LIKED,
    "social_disliked": SocialActionVerb.DISLIKED,
    "social_observed": SocialActionVerb.OBSERVED,
    "social_followed": SocialActionVerb.FOLLOWED,
    "social_blocked": SocialActionVerb.BLOCKED,
}

_TOOL_DESCRIPTIONS: Final[dict[str, str]] = {
    "social_posted": "发布内容到当前 Session 公共广场（board:{session_id}）。",
    "social_replied": "回复某条事件（target_ref 必须是 event_id）。",
    "social_quoted": "转发并评论某条事件（target_ref 必须是 event_id）。",
    "social_liked": "点赞某条事件（target_ref 必须是 event_id）。",
    "social_disliked": "反对某条事件（target_ref 必须是 event_id）。",
    "social_observed": "记录观察结果（target_ref 可为 board/event/agent）。",
    "social_followed": "关注某个实体（target_ref 必须是 agent uuid）。",
    "social_blocked": "拉黑某个实体（target_ref 必须是 agent uuid）。",
}


def build_social_action_tools() -> list[dict[str, Any]]:
    """构造 8 大社交动作 Tool Calling 定义。"""
    tools: list[dict[str, Any]] = []
    for tool_name, args_model in _TOOL_ARGS_MODELS.items():
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": _TOOL_DESCRIPTIONS[tool_name],
                    "parameters": args_model.model_json_schema(),
                },
            }
        )
    return tools


def list_social_action_specs() -> list[dict[str, Any]]:
    """返回前端可消费的社交动作元数据。"""
    items: list[dict[str, Any]] = []
    for tool_name, args_model in _TOOL_ARGS_MODELS.items():
        verb = _TOOL_VERB_MAP[tool_name]
        allowed_topologies = sorted(
            topology.value for topology in SOCIAL_ACTION_TARGET_RULES[verb]
        )
        items.append(
            {
                "tool_name": tool_name,
                "verb": verb.value,
                "description": _TOOL_DESCRIPTIONS[tool_name],
                "allowed_target_topologies": allowed_topologies,
                "parameters_schema": args_model.model_json_schema(),
            }
        )
    return items


def parse_social_action_tool_call(
    *,
    session_id: str,
    tool_name: str,
    arguments: dict[str, Any],
) -> SocialActionCommand:
    """将 Tool Calling 输出解析为统一社交动作命令。"""
    args_model = _TOOL_ARGS_MODELS.get(tool_name)
    verb = _TOOL_VERB_MAP.get(tool_name)
    if args_model is None or verb is None:
        raise InvalidSocialActionToolCallError(f"Unsupported social action tool: {tool_name}")

    try:
        payload = args_model.model_validate(arguments)
    except ValidationError as exc:
        raise InvalidSocialActionToolCallError(
            f"Invalid arguments for tool '{tool_name}': {exc.errors()}",
        ) from exc
    target_ref, details = _to_target_and_details(
        session_id=session_id,
        tool_name=tool_name,
        payload=payload,
    )

    if not is_target_allowed_for_verb(
        verb=verb,
        session_id=session_id,
        target_ref=target_ref,
    ):
        raise InvalidSocialActionToolCallError(
            f"Tool '{tool_name}' target_ref '{target_ref}' violates topology constraint."
        )

    return SocialActionCommand(
        verb=verb,
        target_ref=target_ref,
        details=details,
        inner_thought_brief=payload.inner_thought_brief,
        is_social=True,
    )


def _to_target_and_details(
    *,
    session_id: str,
    tool_name: str,
    payload: _BaseToolArgs,
) -> tuple[str, dict[str, Any]]:
    """将工具参数映射为标准 target_ref 与 details。"""
    if tool_name == "social_posted":
        posted = _require_payload_type(payload, _PostedArgs)
        return build_board_ref(session_id=session_id), {
            "content": posted.content,
            "tags": posted.tags,
        }

    if tool_name == "social_replied":
        replied = _require_payload_type(payload, _RepliedArgs)
        return replied.target_ref, {"content": replied.content}

    if tool_name == "social_quoted":
        quoted = _require_payload_type(payload, _QuotedArgs)
        return quoted.target_ref, {"content": quoted.content}

    if tool_name == "social_liked":
        liked = _require_payload_type(payload, _LikedArgs)
        return liked.target_ref, {}

    if tool_name == "social_disliked":
        disliked = _require_payload_type(payload, _DislikedArgs)
        return disliked.target_ref, {}

    if tool_name == "social_observed":
        observed = _require_payload_type(payload, _ObservedArgs)
        return observed.target_ref, {"internal_thought": observed.internal_thought}

    if tool_name == "social_followed":
        followed = _require_payload_type(payload, _FollowedArgs)
        return followed.target_ref, {}

    blocked = _require_payload_type(payload, _BlockedArgs)
    return blocked.target_ref, {}


def _require_payload_type(payload: _BaseToolArgs, expected_type: type[_BaseToolArgs]) -> _BaseToolArgs:
    """在静态映射约束下做一次运行时类型断言。"""
    if isinstance(payload, expected_type):
        return payload
    raise InvalidSocialActionToolCallError(
        f"Invalid payload type: expected {expected_type.__name__}, got {type(payload).__name__}."
    )


__all__ = [
    "InvalidSocialActionToolCallError",
    "build_social_action_tools",
    "list_social_action_specs",
    "parse_social_action_tool_call",
]
