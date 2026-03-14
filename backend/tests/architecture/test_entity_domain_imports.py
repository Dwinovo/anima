from __future__ import annotations

from pathlib import Path


def test_non_compatibility_layers_import_entity_domain_instead_of_agent_domain() -> None:
    """验证非兼容层代码不再直接依赖 domain.agent。"""
    root = Path("src")
    violations: list[str] = []
    for file_path in root.rglob("*.py"):
        relative = file_path.as_posix()
        if relative.startswith("src/domain/agent/"):
            continue
        content = file_path.read_text(encoding="utf-8")
        if "src.domain.agent." in content:
            violations.append(relative)

    assert violations == []
