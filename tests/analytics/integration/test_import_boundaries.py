"""Repository import-boundary checks for the Analytics public API."""

import ast
from pathlib import Path

from app.utils import get_logger

logger = get_logger(__name__)

_ROOT = Path(__file__).resolve().parents[3]
_ALLOWED_INTERNAL_PREFIXES = (
    _ROOT / "app" / "services" / "analytics",
    _ROOT / "tests" / "analytics" / "unit",
    _ROOT / "tests" / "analytics" / "component",
)


def _is_allowed_internal_consumer(path: Path) -> bool:
    """Return whether a source path may deep-import Analytics internals.

    Args:
        path: Candidate Python source path.

    Returns:
        True for Analytics implementation and focused unit tests.
    """
    return any(path.is_relative_to(prefix) for prefix in _ALLOWED_INTERNAL_PREFIXES)


def test_external_consumers_use_package_root_only() -> None:
    """Production and behavioral evidence never deep-import Analytics."""
    logger.info("Testing Analytics repository import boundary")
    violations: list[str] = []
    paths = tuple((_ROOT / "app").rglob("*.py")) + tuple(
        (_ROOT / "tests").rglob("*.py")
    )
    for path in sorted(paths):
        if _is_allowed_internal_consumer(path):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
                "app.services.analytics."
            ):
                violations.append(f"{path.relative_to(_ROOT)}:{node.lineno}")
    assert violations == []
