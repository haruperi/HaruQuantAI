"""Strategy import and prohibited-capability security tests."""

import ast
from pathlib import Path

from app.utils import get_logger

logger = get_logger(__name__)


def _collect_strategy_import_roots() -> frozenset[str]:
    """Collect production import roots once during test-module discovery."""
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
        text = path.read_text(encoding="utf-8")
        if not any(module in text for module in prohibited):
            continue
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
    return frozenset(imports)


_STRATEGY_IMPORT_ROOTS = _collect_strategy_import_roots()


def test_strategy_has_no_prohibited_direct_imports() -> None:
    """Verify Strategy source imports no direct external-access modules."""
    logger.debug("Testing Strategy prohibited import boundary")
    prohibited = {
        "os",
        "pathlib",
        "random",
        "secrets",
        "socket",
        "subprocess",
        "urllib",
    }
    assert _STRATEGY_IMPORT_ROOTS.isdisjoint(prohibited)
