from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.application.cognition.decision_model import SocialDecisionModel
from src.application.dto.event import EventSearchItem
from src.domain.agent.social_actions import SocialActionCommand, build_board_ref
from src.infrastructure.llm.tool_calling.social_actions import (
    InvalidSocialActionToolCallError,
    build_social_action_tools,
    parse_social_action_tool_call,
)


class SocialAgent(SocialDecisionModel):
    """基于 LangChain Tool Calling 的社交动作决策模型。"""

    def __init__(
        self,
        *,
        model_name: str,
        api_key: str | None = None,
        base_url: str | None = None,
        llm: Any | None = None,
        request_timeout_seconds: float = 30.0,
        temperature: float = 0.7,
    ) -> None:
        """初始化模型客户端，未配置密钥时自动进入降级模式。"""
        self._model_name = model_name
        self._llm = self._build_llm(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            llm=llm,
            request_timeout_seconds=request_timeout_seconds,
            temperature=temperature,
        )
        self._tools = build_social_action_tools()

    async def decide(
        self,
        *,
        session_id: str,
        uuid: str,
        prompt: str,
        profile_payload: dict[str, Any],
        working_memory: list[str],
        observation_items: list[EventSearchItem],
    ) -> SocialActionCommand:
        """调用 LLM 进行工具选择，并转换为统一社交动作命令。"""
        _ = uuid
        if self._llm is None:
            return self._fallback_observed(
                session_id=session_id,
                observation_items=observation_items,
                reason="llm_not_configured",
            )

        try:
            runnable = self._llm.bind_tools(
                self._tools,
                tool_choice="required",
                parallel_tool_calls=False,
            )
            response = await runnable.ainvoke(
                self._build_messages(
                    profile_payload=profile_payload,
                    prompt=prompt,
                    working_memory=working_memory,
                    observation_items=observation_items,
                )
            )
        except Exception:
            return self._fallback_observed(
                session_id=session_id,
                observation_items=observation_items,
                reason="llm_request_failed",
            )

        tool_call = self._extract_first_tool_call(response)
        if tool_call is None:
            return self._fallback_observed(
                session_id=session_id,
                observation_items=observation_items,
                reason="llm_no_tool_call",
            )

        tool_name, arguments = tool_call
        try:
            return parse_social_action_tool_call(
                session_id=session_id,
                tool_name=tool_name,
                arguments=arguments,
            )
        except InvalidSocialActionToolCallError:
            return self._fallback_observed(
                session_id=session_id,
                observation_items=observation_items,
                reason="llm_invalid_tool_call",
            )

    @staticmethod
    def _build_llm(
        *,
        model_name: str,
        api_key: str | None,
        base_url: str | None,
        llm: Any | None,
        request_timeout_seconds: float,
        temperature: float,
    ) -> Any | None:
        """构建 ChatOpenAI 客户端或返回注入的测试替身。"""
        if llm is not None:
            return llm
        if api_key is None or not api_key.strip():
            return None

        kwargs: dict[str, Any] = {
            "model": model_name,
            "api_key": api_key,
            "timeout": request_timeout_seconds,
            "temperature": temperature,
        }
        if base_url is not None and base_url.strip():
            kwargs["base_url"] = base_url.strip()
        return ChatOpenAI(**kwargs)

    @classmethod
    def _build_messages(
        cls,
        *,
        profile_payload: dict[str, Any],
        prompt: str,
        working_memory: list[str],
        observation_items: list[EventSearchItem],
    ) -> list[SystemMessage | HumanMessage]:
        """构建聊天消息：Profile 进入 system，上下文进入 human。"""
        human_content = prompt.strip()
        if not human_content:
            human_content = cls._build_human_context(
                working_memory=working_memory,
                observation_items=observation_items,
            )

        return [
            SystemMessage(content=cls._build_system_profile(profile_payload=profile_payload)),
            HumanMessage(content=human_content),
        ]

    @staticmethod
    def _build_system_profile(*, profile_payload: dict[str, Any]) -> str:
        """将注册态 Profile 字典映射为 system message。"""
        if profile_payload:
            return json.dumps(profile_payload, ensure_ascii=False, separators=(",", ":"))
        return "你是一个社交智能体。"

    @staticmethod
    def _build_human_context(
        *,
        working_memory: list[str],
        observation_items: list[EventSearchItem],
    ) -> str:
        """拼接 human message 上下文。"""
        memory_lines = "\n".join(f"- {item}" for item in working_memory) if working_memory else "- (empty)"
        if observation_items:
            observation_lines = "\n".join(
                f"- ({item.world_time}) [{item.verb}] {item.subject_uuid} -> {item.target_ref}: "
                f"{json.dumps(item.details, ensure_ascii=False)}"
                for item in observation_items
            )
        else:
            observation_lines = "- (empty)"

        return "\n".join(
            [
                "# [RECENT MEMORY]",
                memory_lines,
                "",
                "# [OBSERVATION]",
                observation_lines,
            ]
        )

    @classmethod
    def _extract_first_tool_call(cls, response: Any) -> tuple[str, dict[str, Any]] | None:
        """从 LangChain 消息中提取首个工具调用。"""
        tool_calls = cls._read_field(response, "tool_calls")
        if not isinstance(tool_calls, list) or not tool_calls:
            return None

        tool_call = tool_calls[0]
        tool_name = cls._read_field(tool_call, "name")
        raw_arguments = cls._read_field(tool_call, "args")
        if raw_arguments is None:
            function = cls._read_field(tool_call, "function")
            if function is not None:
                tool_name = tool_name or cls._read_field(function, "name")
                raw_arguments = cls._read_field(function, "arguments")

        if not isinstance(tool_name, str) or not tool_name:
            return None

        arguments = cls._parse_arguments(raw_arguments)
        if arguments is None:
            return None
        return tool_name, arguments

    @staticmethod
    def _read_field(payload: Any, field_name: str) -> Any:
        """兼容对象/字典两种结构读取字段。"""
        if isinstance(payload, dict):
            return payload.get(field_name)
        return getattr(payload, field_name, None)

    @staticmethod
    def _parse_arguments(raw_arguments: Any) -> dict[str, Any] | None:
        """解析工具调用参数，支持 JSON 字符串与字典。"""
        if isinstance(raw_arguments, dict):
            return raw_arguments
        if not isinstance(raw_arguments, str):
            return None
        try:
            parsed = json.loads(raw_arguments)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            return parsed
        return None

    @staticmethod
    def _fallback_observed(
        *,
        session_id: str,
        observation_items: list[EventSearchItem],
        reason: str,
    ) -> SocialActionCommand:
        """在 LLM 不可用或输出异常时降级为 OBSERVED 动作。"""
        latest_verb = observation_items[0].verb if observation_items else None
        if isinstance(latest_verb, str) and latest_verb:
            inner_thought_brief = f"先观察{latest_verb}后的局势"
        else:
            inner_thought_brief = "先观察局势"
        inner_thought_brief = inner_thought_brief[:48]

        return parse_social_action_tool_call(
            session_id=session_id,
            tool_name="social_observed",
            arguments={
                "target_ref": build_board_ref(session_id=session_id),
                "internal_thought": f"fallback:{reason}",
                "inner_thought_brief": inner_thought_brief,
            },
        )


__all__ = ["SocialAgent"]
