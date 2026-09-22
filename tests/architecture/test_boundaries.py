"""Check the approved S2 package boundaries without importing providers."""

import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[2] / "app"


def test_s2_application_roots_are_exact() -> None:
    """Only the approved kernel, host, plugins, and UI roots exist."""
    names = {
        path.name
        for path in APP.iterdir()
        if path.is_file() or path.name == "ui" or any(path.rglob("*.py"))
    }
    assert names == {"__init__.py", "host", "kernel", "plugins", "ui"}


def test_s5_python_owner_files_are_exact() -> None:
    assert {path.name for path in (APP / "kernel").glob("*.py")} == {
        "__init__.py",
        "bootstrapper.py",
        "capability.py",
        "context.py",
        "feature.py",
    }
    assert {path.name for path in (APP / "host").glob("*.py")} == {
        "__init__.py",
        "artifacts.py",
        "bootstrap.py",
        "catalog.py",
        "execution.py",
        "gateway.py",
        "jobs.py",
        "storage.py",
        "telemetry.py",
        "workers.py",
    }
    assert {path.name for path in (APP / "plugins").glob("*.py")} == {
        "__init__.py",
        "algebra.py",
        "lowering.py",
        "schema.py",
        "spec.py",
        "wire.py",
    }
    assert {path.name for path in (APP / "plugins" / "indicators").glob("*.py")} == {
        "__init__.py",
        "rsi.py",
    }
    assert {path.name for path in (APP / "plugins" / "comparisons").glob("*.py")} == {
        "__init__.py",
        "greater_than.py",
    }
    assert {path.name for path in (APP / "plugins" / "exporters").glob("*.py")} == {
        "__init__.py",
        "python.py",
    }
    assert {path.name for path in (APP / "plugins" / "workspaces").glob("*.py")} == {
        "__init__.py",
        "builder.py",
        "optimizer.py",
        "results.py",
        "retester.py",
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


_ALLOWED_PLUGIN_IMPORTS: dict[str, tuple[str, ...]] = {
    "schema": (),
    "lowering": ("app.plugins.schema",),
    "spec": ("app.plugins.schema", "app.plugins.lowering"),
    "algebra": ("app.plugins.schema", "app.plugins.lowering", "app.plugins.spec"),
    "wire": (
        "app.plugins.schema",
        "app.plugins.lowering",
        "app.plugins.spec",
        "app.plugins.algebra",
    ),
}


def _check_plugin_import(path: Path, module_name: str, name: str) -> None:
    assert not name.startswith(("app.host.", "app.ui.")), (
        f"{path} imported host/ui: {name}"
    )
    if name.startswith("app.kernel."):
        assert name == "app.kernel.capability" and module_name == "spec", (
            f"Forbidden kernel import in {path}: {name}"
        )
    if name.startswith("app.plugins."):
        allowed = _ALLOWED_PLUGIN_IMPORTS.get(module_name, ())
        assert name.startswith(allowed), f"{module_name}.py may not import {name}"


def test_shared_plugins_acyclic_import_dag() -> None:
    """Enforce the strict acyclic dependency DAG in app/plugins/."""
    for path in (APP / "plugins").glob("*.py"):
        if path.name == "__init__.py":
            continue
        module_name = path.stem
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    _check_plugin_import(path, module_name, alias.name)
            elif isinstance(node, ast.ImportFrom):
                assert node.level == 0, f"Relative import in {path}"
                _check_plugin_import(path, module_name, node.module or "")


def test_concrete_plugins_isolation() -> None:
    """Ensure concrete plugins import only the shared metamodel and stdlib."""
    allowed_metamodel = (
        "app.plugins.schema",
        "app.plugins.lowering",
        "app.plugins.spec",
        "app.plugins.algebra",
        "app.plugins.wire",
    )
    for family in ("indicators", "comparisons", "exporters", "workspaces"):
        for path in (APP / "plugins" / family).glob("*.py"):
            if path.name == "__init__.py":
                continue
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                targets: list[str] = []
                if isinstance(node, ast.Import):
                    targets = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    assert node.level == 0, f"Relative import in {path}"
                    targets = [node.module or ""]
                for target in targets:
                    assert not target.startswith(
                        ("app.host.", "app.ui.", "app.kernel.")
                    ), f"Forbidden import in {path}: {target}"
                    if target.startswith("app.plugins."):
                        assert target.startswith(allowed_metamodel), (
                            f"Cross-plugin import in {path}: {target}"
                        )
