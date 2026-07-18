"""Strategy import and prohibited-capability security tests."""

import ast
from pathlib import Path

from app.utils import logger


def test_strategy_has_no_prohibited_direct_imports() -> None:
    """Verify Strategy source imports no direct external-access modules."""
    logger.debug("Testing Strategy prohibited import boundary")
    root = Path("app/services/strategy")
    prohibited = {
        "os",
        "pathlib",
        "random",
        "secrets",
        "socket",
        "subprocess",
        "urllib",
    }
    imports: set[str] = set()
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
    assert imports.isdisjoint(prohibited)
