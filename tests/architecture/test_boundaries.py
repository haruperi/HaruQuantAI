"""Check the approved S1 package boundaries without importing providers."""

import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[2] / "app"


def test_s1_application_roots_are_exact() -> None:
    """Only the approved kernel, host foundation, and UI roots exist."""
    names = {
        path.name
        for path in APP.iterdir()
        if path.is_file() or path.name == "ui" or any(path.rglob("*.py"))
    }
    assert names == {"__init__.py", "host", "kernel", "ui"}


def test_s1_python_owner_files_are_exact() -> None:
    assert {path.name for path in (APP / "kernel").glob("*.py")} == {
        "__init__.py",
        "bootstrapper.py",
        "capability.py",
        "context.py",
        "feature.py",
    }
    assert {path.name for path in (APP / "host").glob("*.py")} == {
        "__init__.py",
        "bootstrap.py",
        "telemetry.py",
    }


def test_package_initializers_are_docstring_only() -> None:
    for path in APP.rglob("__init__.py"):
        body = ast.parse(path.read_text(encoding="utf-8")).body
        assert not body or (
            len(body) == 1
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ), str(path)


def test_kernel_has_no_business_or_third_party_imports() -> None:
    import sys

    for path in (APP / "kernel").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                assert node.level == 0, str(path)
                names = [node.module or ""]
            for name in names:
                assert name.startswith("app.kernel.") or name.split(".")[0] in (
                    sys.stdlib_module_names
                ), (path, name)
