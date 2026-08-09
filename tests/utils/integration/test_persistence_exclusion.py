"""Persistence ownership exclusion proof for Utils."""

import ast
from pathlib import Path


def test_utils_opens_no_database_or_transaction_dependency() -> None:
    """Utils remains independent of persistence infrastructure."""
    root = Path(__file__).parents[3] / "app" / "utils"
    forbidden = {"sqlite3", "app.services.data"}
    imports: set[str] = set()
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
    assert not any(
        name == item or name.startswith(f"{item}.")
        for name in imports
        for item in forbidden
    )
