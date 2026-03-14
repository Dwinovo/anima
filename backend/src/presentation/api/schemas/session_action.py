from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from jsonschema import Draft202012Validator, SchemaError
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.domain.session.actions import SessionAction

VERB_NAMESPACE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")


def _collect_missing_property_descriptions(
    schema: dict[str, Any],
    *,
    path: str,
) -> list[str]:
    """递归收集缺失 description 的参数路径。"""
    missing: list[str] = []
    schema_type = schema.get("type")

    if schema_type == "object":
        properties = schema.get("properties")
        if isinstance(properties, dict):
            for property_name, property_schema in properties.items():
                property_path = f"{path}.properties.{property_name}"
                if isinstance(property_schema, dict):
                    description = property_schema.get("description")
                    if not isinstance(description, str) or not description.strip():
                        missing.append(property_path)
                    missing.extend(
                        _collect_missing_property_descriptions(
                            property_schema,
                            path=property_path,
                        )
                    )
                else:
                    # 非法 property schema 会由 Draft202012Validator 捕获，这里仅兜底提示。
                    missing.append(property_path)

    if schema_type == "array":
        items_schema = schema.get("items")
        if isinstance(items_schema, dict):
            missing.extend(
                _collect_missing_property_descriptions(
                    items_schema,
                    path=f"{path}.items",
                )
            )
        elif isinstance(items_schema, list):
            for index, item_schema in enumerate(items_schema):
                if isinstance(item_schema, dict):
                    missing.extend(
                        _collect_missing_property_descriptions(
                            item_schema,
                            path=f"{path}.items[{index}]",
                        )
                    )

    for keyword in ("allOf", "anyOf", "oneOf"):
        candidates = schema.get(keyword)
        if isinstance(candidates, list):
            for index, candidate_schema in enumerate(candidates):
                if isinstance(candidate_schema, dict):
                    missing.extend(
                        _collect_missing_property_descriptions(
                            candidate_schema,
                            path=f"{path}.{keyword}[{index}]",
                        )
                    )

    return missing


def _fill_missing_property_descriptions(
    schema: dict[str, Any],
) -> dict[str, Any]:
    """为历史 schema 自动补齐缺失的参数 description。"""
    normalized = deepcopy(schema)

    def _fill(node: dict[str, Any]) -> None:
        schema_type = node.get("type")

        if schema_type == "object":
            properties = node.get("properties")
            if isinstance(properties, dict):
                for property_name, property_schema in properties.items():
                    if isinstance(property_schema, dict):
                        description = property_schema.get("description")
                        if not isinstance(description, str) or not description.strip():
                            property_schema["description"] = f"{property_name} parameter"
                        _fill(property_schema)

        if schema_type == "array":
            items_schema = node.get("items")
            if isinstance(items_schema, dict):
                _fill(items_schema)
            elif isinstance(items_schema, list):
                for item_schema in items_schema:
                    if isinstance(item_schema, dict):
                        _fill(item_schema)

        for keyword in ("allOf", "anyOf", "oneOf"):
            candidates = node.get(keyword)
            if isinstance(candidates, list):
                for candidate_schema in candidates:
                    if isinstance(candidate_schema, dict):
                        _fill(candidate_schema)

    _fill(normalized)
    return normalized


class SessionActionSchema(BaseModel):
    """Session actions 的共享表示。"""

    verb: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="动作类型，必须采用 domain.verb 命名空间格式。",
        examples=["social.posted"],
    )
    description: str | None = Field(
        default=None,
        max_length=256,
        description="动作说明。",
    )
    details_schema: dict[str, Any] = Field(
        ...,
        description="动作 details 的 JSON Schema（当前要求 type=object）。",
    )

    @field_validator("verb")
    @classmethod
    def _validate_verb_namespace(cls, value: str) -> str:
        """校验 verb 必须满足 domain.verb 命名空间格式。"""
        if VERB_NAMESPACE_PATTERN.match(value) is None:
            raise ValueError("verb 格式非法，必须为 domain.verb。")
        return value

    @field_validator("details_schema")
    @classmethod
    def _validate_details_schema(cls, value: dict[str, Any]) -> dict[str, Any]:
        """校验 details_schema 至少是 object schema。"""
        if value.get("type") != "object":
            raise ValueError("details_schema.type 必须为 object。")
        try:
            Draft202012Validator.check_schema(value)
        except SchemaError as exc:
            raise ValueError(f"details_schema 非法: {exc.message}") from exc
        missing_description_paths = _collect_missing_property_descriptions(
            value,
            path="details_schema",
        )
        if missing_description_paths:
            missing_paths = ", ".join(sorted(missing_description_paths))
            raise ValueError(
                "details_schema.properties 中每个参数都必须提供非空 description。"
                f"缺失: {missing_paths}"
            )
        return value

    def to_domain(self) -> SessionAction:
        """转为领域对象。"""
        return SessionAction(
            verb=self.verb,
            description=self.description,
            details_schema=dict(self.details_schema),
        )

    @classmethod
    def from_domain(cls, action: SessionAction) -> SessionActionSchema:
        """由领域对象构造响应模型。"""
        normalized_schema = _fill_missing_property_descriptions(
            dict(action.details_schema)
        )
        return cls(
            verb=action.verb,
            description=action.description,
            details_schema=normalized_schema,
        )

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )
