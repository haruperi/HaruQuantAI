"""Static API import-boundary evidence."""

import ast
from pathlib import Path

_API_ROOT = Path(__file__).resolve().parents[3] / "app" / "services" / "api"


def test_api_uses_only_owner_package_roots() -> None:
    """API production modules must not deep-import another business domain."""
    violations: list[str] = []
    for source_path in sorted(_API_ROOT.rglob("*.py")):
        tree = ast.parse(
            source_path.read_text(encoding="utf-8"), source_path.as_posix()
        )
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or node.module is None:
                continue
            module = node.module
            if module.startswith("app.agentic."):
                violations.append(f"{source_path}:{node.lineno}:{module}")
                continue
            if module.startswith("app.services."):
                parts = module.split(".")
                if len(parts) > 3 and parts[2] != "api":
                    violations.append(f"{source_path}:{node.lineno}:{module}")
    assert violations == []
