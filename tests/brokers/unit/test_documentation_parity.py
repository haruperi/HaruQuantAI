"""Validate Brokers feature-registry and active-document parity."""

import ast
import re
from pathlib import Path


def test_brokers_readme_has_one_reconciled_completed_registry() -> None:
    """Require one feature, folder, and usage program for every registry row."""
    readme = Path("app/services/brokers/README.md").read_text(encoding="utf-8")
    assert readme.count("### Feature Registry") == 1
    rows = re.findall(
        r"\| Completed \| `(?P<id>FEAT-BRK-\d{2})`[^|]*"
        r"\| `(?P<folder>[^`]+/)`[^|]*\|[^|]*\|[^|]*"
        r"\| `(?P<usage>tests/brokers/usage/features/\d{2}_[^`]+\.py)`\s+\|",
        readme,
    )
    assert [feature_id for feature_id, _, _ in rows] == [
        *(f"FEAT-BRK-{index:02d}" for index in range(11)),
        "FEAT-BRK-18",
    ]
    assert len({folder for _, folder, _ in rows}) == 12
    assert len({usage for _, _, usage in rows}) == 12
    for _, folder, usage in rows:
        assert (Path("app/services/brokers") / folder).is_dir()
        assert Path(usage).is_file()
    assert "aggregates midpoint bars locally" not in readme
    assert "without a probe" not in readme
    assert "offline transport" not in readme
    assert "reject live environments" in readme
    assert re.search(r"never\s+transmit broker mutations", readme)
    assert "- [ ]" not in readme


def test_brokers_functions_have_applicable_google_docstring_sections() -> None:
    """Require Args, Returns, and Raises sections where behavior needs them."""
    failures: list[str] = []
    for path in sorted(Path("app/services/brokers").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            docstring = ast.get_docstring(node) or ""
            parameters = [
                argument.arg
                for argument in (
                    *node.args.posonlyargs,
                    *node.args.args,
                    *node.args.kwonlyargs,
                )
                if argument.arg not in {"self", "cls"}
            ]
            if node.args.vararg is not None:
                parameters.append(node.args.vararg.arg)
            if node.args.kwarg is not None:
                parameters.append(node.args.kwarg.arg)
            behavior_nodes: list[ast.AST] = []
            pending = list(node.body)
            while pending:
                child = pending.pop()
                behavior_nodes.append(child)
                if not isinstance(
                    child,
                    (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda),
                ):
                    pending.extend(ast.iter_child_nodes(child))
            required = {
                "Args:": bool(parameters),
                "Returns:": any(
                    isinstance(child, ast.Return) and child.value is not None
                    for child in behavior_nodes
                ),
                "Raises:": any(
                    isinstance(child, ast.Raise) for child in behavior_nodes
                ),
            }
            missing = [
                section
                for section, applies in required.items()
                if applies and section not in docstring
            ]
            if missing:
                failures.append(
                    f"{path}:{node.lineno}:{node.name}: {', '.join(missing)}"
                )
    assert not failures, "\n".join(failures)
