from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pytest

from src.application.dto.event import EventSearchItem
from src.domain.agent.social_actions import SocialActionVerb
from src.infrastructure.llm.social_agent import SocialAgent


@dataclass(slots=True)
class _FakeResponse:
    tool_calls: list[dict[str, Any]] | None


class _FakeRunnable:
    def __init__(self, response: _FakeResponse, *, owner: "_FakeLLM") -> None:
        """初始化可执行对象测试替身。"""
        self._response = response
        self._owner = owner

    async def ainvoke(self, messages: Any) -> _FakeResponse:
        """记录消息并返回预设响应。"""
        self._owner.last_messages = messages
        return self._response


class _FakeLLM:
    def __init__(self, response: _FakeResponse) -> None:
        """初始化 LLM 测试替身。"""
        self._response = response
        self.last_bind_kwargs: dict[str, Any] | None = None
        self.last_messages: Any = None

    def bind_tools(self, tools: Any, **kwargs: Any) -> _FakeRunnable:
        """记录工具绑定参数并返回可执行对象。"""
        self.last_bind_kwargs = {
            "tools": tools,
            "kwargs": kwargs,
        }
        return _FakeRunnable(self._response, owner=self)


def _build_observation_items() -> list[EventSearchItem]:
    """构造测试用 observation 事件列表。"""
    return [
        EventSearchItem(
            event_id="event_001",
            world_time=100,
            verb="POSTED",
            subject_uuid="agent_b",
            target_ref="board:session_demo",
            details={"content": "hello"},
            schema_version=1,
            is_social=True,
        )
    ]


@pytest.mark.asyncio
async def test_social_agent_parses_tool_call_response() -> None:
    """验证 LLM 合法工具调用会被解析为统一社交动作命令。"""
    fake_response = _FakeResponse(
        tool_calls=[
            {
                "name": "social_replied",
                "args": {
                    "target_ref": "event_001",
                    "content": "收到",
                    "inner_thought_brief": "先回复确认",
                },
            }
        ]
    )
    model = SocialAgent(
        model_name="gpt-4o",
        llm=_FakeLLM(fake_response),
    )

    command = await model.decide(
        session_id="session_demo",
        uuid="agent_a",
        prompt="test prompt",
        profile_payload={"name": "Alice"},
        working_memory=["先观察局势"],
        observation_items=_build_observation_items(),
    )

    assert command.verb is SocialActionVerb.REPLIED
    assert command.target_ref == "event_001"
    assert command.details["content"] == "收到"
    assert command.inner_thought_brief == "先回复确认"
    assert command.is_social is True


@pytest.mark.asyncio
async def test_social_agent_falls_back_when_llm_unavailable() -> None:
    """验证 LLM 不可用时会降级为 OBSERVED 动作。"""
    model = SocialAgent(
        model_name="gpt-4o",
        llm=None,
    )

    command = await model.decide(
        session_id="session_demo",
        uuid="agent_a",
        prompt="test prompt",
        profile_payload={"name": "Alice"},
        working_memory=["先观察局势"],
        observation_items=_build_observation_items(),
    )

    assert command.verb is SocialActionVerb.OBSERVED
    assert command.target_ref == "board:session_demo"
    assert "internal_thought" in command.details
    assert command.inner_thought_brief.startswith("先观察")


@pytest.mark.asyncio
async def test_social_agent_uses_registered_profile_dict_as_system_and_context_as_human_message() -> None:
    """验证注册态 profile dict 进入 system message，上下文拼接进入 human message。"""
    fake_response = _FakeResponse(
        tool_calls=[
            {
                "name": "social_observed",
                "args": {
                    "target_ref": "board:session_demo",
                    "internal_thought": "先观察",
                    "inner_thought_brief": "先观察局势",
                },
            }
        ]
    )
    fake_llm = _FakeLLM(fake_response)
    model = SocialAgent(
        model_name="gpt-4o",
        llm=fake_llm,
    )

    profile_payload = {
        "name": "Alice",
        "display_name": "Alice#10001",
        "profile": {
            "prompt": "你叫Alice#10001，擅长理性讨论，先观察再行动。",
            "traits": ["rational", "curious"],
        },
    }

    await model.decide(
        session_id="session_demo",
        uuid="agent_a",
        prompt="# [RECENT MEMORY]\n- 记忆A\n\n# [OBSERVATION]\n- (100) [POSTED] agent_b -> board:session_demo",
        profile_payload=profile_payload,
        working_memory=["记忆A"],
        observation_items=_build_observation_items(),
    )

    assert fake_llm.last_messages is not None
    assert len(fake_llm.last_messages) == 2
    system_message = fake_llm.last_messages[0]
    human_message = fake_llm.last_messages[1]
    assert json.loads(str(system_message.content)) == profile_payload
    assert "[RECENT MEMORY]" in str(human_message.content)
    assert "[OBSERVATION]" in str(human_message.content)
    assert "必须且只允许调用一个工具" not in str(system_message.content)
