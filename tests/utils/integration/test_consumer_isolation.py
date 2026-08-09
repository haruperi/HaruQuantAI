"""Cross-domain consumer-isolation proof for the Utils public boundary.

AST-scans audited-domain production and public evidence sources to keep every
consumer on the Utils package root: no deep imports and no private-attribute
mutation. Parses only; imports nothing from ``app.services``.
"""

import ast
from pathlib import Path

import app.utils


def test_no_consumer_imports_or_mutates_utils_internals() -> None:
    """Keep audited-domain production and public evidence on the Utils root."""
    source_root = Path(app.utils.__file__).parent
    repository_root = source_root.parents[1]
    offenders: list[str] = []
    source_files = [
        *(repository_root / "app" / "services" / "brokers").rglob("*.py"),
        *(repository_root / "app" / "services" / "data").rglob("*.py"),
        *(repository_root / "tests" / "brokers" / "integration").rglob("*.py"),
        *(repository_root / "tests" / "brokers" / "usage").rglob("*.py"),
        *(repository_root / "tests" / "data" / "integration").rglob("*.py"),
        *(repository_root / "tests" / "data" / "usage").rglob("*.py"),
        *(repository_root / "tests" / "brokers").glob("wf_*.py"),
        repository_root / "tests" / "brokers" / "wf_support.py",
    ]
    for source_file in source_files:
        if not source_file.is_file():
            continue
        if source_root in source_file.parents or source_file == source_root:
            continue
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
        relative = source_file.relative_to(repository_root).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                offenders.extend(
                    f"{relative}:{node.lineno} imports {alias.name}"
                    for alias in node.names
                    if alias.name.count(".") > 1 and alias.name.startswith("app.utils.")
                )
            elif (
                isinstance(node, ast.ImportFrom)
                and node.module is not None
                and node.module.count(".") > 1
                and node.module.startswith("app.utils.")
            ):
                offenders.append(f"{relative}:{node.lineno} imports from {node.module}")
            elif isinstance(node, ast.Assign):
                offenders.extend(
                    f"{relative}:{node.lineno} assigns {target.attr}"
                    for target in node.targets
                    if isinstance(target, ast.Attribute)
                    and target.attr.startswith("_")
                    and "app.utils" in ast.unparse(target.value)
                )
    assert not offenders, "\n" + "\n".join(offenders)
