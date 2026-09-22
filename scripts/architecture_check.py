"""Check architecture invariants of the approved S2 metamodel and host foundation."""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import override

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_ROOT = REPO_ROOT / "app"
UI_SOURCE_ROOT = APP_ROOT / "ui" / "src"

FRONTEND_SOURCE_SUFFIXES = frozenset({".js", ".jsx", ".ts", ".tsx"})
CURRENT_APP_ROOTS = frozenset({"__init__.py", "host", "kernel", "plugins", "ui"})
CURRENT_KERNEL_FILES = frozenset(
    {"__init__.py", "bootstrapper.py", "capability.py", "context.py", "feature.py"}
)
CURRENT_HOST_FILES = frozenset(
    {
        "__init__.py",
        "bootstrap.py",
        "catalog.py",
        "execution.py",
        "gateway.py",
        "telemetry.py",
    }
)
CURRENT_PLUGINS_FILES = frozenset(
    {
        "__init__.py",
        "algebra.py",
        "lowering.py",
        "schema.py",
        "spec.py",
        "wire.py",
    }
)
CURRENT_PLUGIN_FAMILIES: dict[str, frozenset[str]] = {
    "indicators": frozenset({"__init__.py", "rsi.py"}),
    "comparisons": frozenset({"__init__.py", "greater_than.py"}),
    "exporters": frozenset({"__init__.py", "python.py"}),
    "workspaces": frozenset({"__init__.py", "builder.py", "results.py"}),
}
_SHARED_METAMODEL_PREFIXES = (
    "app.plugins.schema",
    "app.plugins.lowering",
    "app.plugins.spec",
    "app.plugins.algebra",
    "app.plugins.wire",
)
_ALLOWED_PLUGIN_IMPORTS: dict[str, tuple[str, ...]] = {
    "schema.py": (),
    "lowering.py": ("app.plugins.schema",),
    "spec.py": ("app.plugins.schema", "app.plugins.lowering"),
    "algebra.py": (
        "app.plugins.schema",
        "app.plugins.lowering",
        "app.plugins.spec",
    ),
    "wire.py": (
        "app.plugins.schema",
        "app.plugins.lowering",
        "app.plugins.spec",
        "app.plugins.algebra",
    ),
}
FORBIDDEN_APP_ROOTS = frozenset(
    {
        "api",
        "contracts",
        "main.py",
        "registry.py",
        "services",
        "workspaces",
    }
)
FORBIDDEN_XML_MODULES = frozenset({"defusedxml", "lxml", "xml", "xmltodict"})
XML_LITERAL_PATTERN = re.compile(
    r"(?:application|text)/xml|[\"'`][^\"'`\r\n]*\.xml(?:[?#][^\"'`\r\n]*)?[\"'`]",
    re.IGNORECASE,
)
FRONTEND_XML_IMPLEMENTATION_PATTERN = re.compile(
    r"\b(?:DOMParser|XMLSerializer)\b|"
    r"(?:fast-xml-parser|xml2js|@xmldom/xmldom)",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class ArchitecturalViolation:
    """Describe one source-bound architecture violation."""

    file_path: Path
    line_number: int
    rule: str
    message: str


def _app_parts(file_path: Path) -> tuple[str, ...]:
    """Return path components beginning at the application package."""
    parts = file_path.resolve().parts
    if "app" not in parts:
        return ()
    return parts[parts.index("app") :]


def _is_docstring_only(module: ast.Module) -> bool:
    """Return whether a module is empty or contains only one docstring."""
    if not module.body:
        return True
    return (
        len(module.body) == 1
        and isinstance(module.body[0], ast.Expr)
        and isinstance(module.body[0].value, ast.Constant)
        and isinstance(module.body[0].value.value, str)
    )


def _dotted_name(node: ast.expr) -> str | None:
    """Return a dotted attribute chain when it is rooted in a name."""
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    parts.append(current.id)
    return ".".join(reversed(parts))


class ArchitecturalVisitor(ast.NodeVisitor):
    """Enforce Python invariants retained during the backend reset."""

    def __init__(self, file_path: Path) -> None:
        """Initialize the visitor for one source file."""
        self.file_path = file_path
        parts = _app_parts(file_path)
        self._depth = 0
        self._is_kernel = len(parts) > 1 and parts[1] == "kernel"
        self._is_host_bootstrap = (
            len(parts) == 3 and parts[1] == "host" and parts[2] == "bootstrap.py"
        )
        self._is_gateway = (
            len(parts) == 3 and parts[1] == "host" and parts[2] == "gateway.py"
        )
        self._is_host_owner = len(parts) > 2 and parts[1] == "host"
        self._is_plugins = len(parts) > 1 and parts[1] == "plugins"
        self._is_shared_plugins = len(parts) == 3 and parts[1] == "plugins"
        self._is_concrete_plugin = len(parts) == 4 and parts[1] == "plugins"
        self._plugin_module_name = (
            parts[2] if len(parts) == 3 and parts[1] == "plugins" else None
        )
        self._host_module_aliases: set[str] = set()
        self.violations: list[ArchitecturalViolation] = []

    def check_module(self, node: ast.Module) -> None:
        """Check package initializer purity."""
        if self.file_path.name == "__init__.py" and not _is_docstring_only(node):
            statement = node.body[1] if len(node.body) > 1 else node.body[0]
            self.violations.append(
                ArchitecturalViolation(
                    self.file_path,
                    statement.lineno,
                    "ARCH-001-INIT-PURITY",
                    "__init__.py must be empty or docstring-only.",
                )
            )

    def _check_plugins_import(self, target: str, line_number: int) -> None:
        if target.startswith(("app.host.", "app.ui.")):
            self.violations.append(
                ArchitecturalViolation(
                    self.file_path,
                    line_number,
                    "ARCH-013-PLUGIN-PURITY",
                    f"Plugins must not import host or UI: {target}",
                )
            )
        if target.startswith("app.kernel."):
            is_valid_spec_cap = (
                self._plugin_module_name == "spec.py"
                and target == "app.kernel.capability"
            )
            if not is_valid_spec_cap:
                self.violations.append(
                    ArchitecturalViolation(
                        self.file_path,
                        line_number,
                        "ARCH-013-PLUGIN-PURITY",
                        f"Plugin cannot import kernel: {target}",
                    )
                )
        if target.startswith("app.plugins."):
            if self._is_shared_plugins:
                allowed_prefixes = _ALLOWED_PLUGIN_IMPORTS.get(
                    self._plugin_module_name or "", ()
                )
                if not target.startswith(allowed_prefixes):
                    self.violations.append(
                        ArchitecturalViolation(
                            self.file_path,
                            line_number,
                            "ARCH-014-PLUGIN-DAG",
                            f"{self._plugin_module_name} may not import {target}",
                        )
                    )
            elif self._is_concrete_plugin:
                if not target.startswith(_SHARED_METAMODEL_PREFIXES):
                    self.violations.append(
                        ArchitecturalViolation(
                            self.file_path,
                            line_number,
                            "ARCH-014-PLUGIN-DAG",
                            f"Concrete plugin may not import {target}",
                        )
                    )

    def _check_import(self, target: str, line_number: int) -> None:
        """Check kernel purity, plugin acyclic DAG, and XML interchange imports."""
        root = target.split(".", maxsplit=1)[0]
        if root in FORBIDDEN_XML_MODULES:
            self.violations.append(
                ArchitecturalViolation(
                    self.file_path,
                    line_number,
                    "ARCH-009-JSON-ONLY",
                    f"XML interchange import is prohibited: {target}",
                )
            )
        if self._is_kernel and not (
            target.startswith("app.kernel.") or root in sys.stdlib_module_names
        ):
            self.violations.append(
                ArchitecturalViolation(
                    self.file_path,
                    line_number,
                    "ARCH-004-KERNEL-PURITY",
                    f"Kernel imports must be standard-library or app.kernel: {target}",
                )
            )
        if self._is_plugins:
            self._check_plugins_import(target, line_number)
        if (
            self._is_gateway
            and self._depth == 0
            and target.startswith(("starlette", "uvicorn"))
        ):
            self.violations.append(
                ArchitecturalViolation(
                    self.file_path,
                    line_number,
                    "ARCH-015-GATEWAY-LAZY-IMPORTS",
                    "Gateway must not import optional server dependencies at "
                    f"module level: {target}",
                )
            )

    @override
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track nesting depth across function bodies."""
        self._depth += 1
        self.generic_visit(node)
        self._depth -= 1

    @override
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Track nesting depth across async function bodies."""
        self._depth += 1
        self.generic_visit(node)
        self._depth -= 1

    @override
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Track nesting depth across class definitions."""
        self._depth += 1
        self.generic_visit(node)
        self._depth -= 1

    @override
    def visit_Import(self, node: ast.Import) -> None:
        """Check every direct import."""
        for alias in node.names:
            self._check_import(alias.name, node.lineno)
            if (
                self._is_host_owner
                and not self._is_host_bootstrap
                and alias.name.startswith("app.host.")
            ):
                self._host_module_aliases.add(alias.asname or alias.name)
        self.generic_visit(node)

    @override
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check every from-import."""
        if node.level:
            if self._is_kernel or self._is_plugins:
                self.violations.append(
                    ArchitecturalViolation(
                        self.file_path,
                        node.lineno,
                        "ARCH-004-KERNEL-PURITY"
                        if self._is_kernel
                        else "ARCH-013-PLUGIN-PURITY",
                        "Application source must use absolute imports.",
                    )
                )
        else:
            self._check_import(node.module or "", node.lineno)
            if (
                self._is_host_owner
                and not self._is_host_bootstrap
                and (node.module or "").startswith("app.host.")
            ):
                for alias in node.names:
                    if alias.name.startswith("_"):
                        self.violations.append(
                            ArchitecturalViolation(
                                self.file_path,
                                node.lineno,
                                "ARCH-011-HOST-PRIVATE",
                                "Only host/bootstrap.py may import another "
                                "owner's private construction symbols.",
                            )
                        )
            if (
                self._is_host_owner
                and not self._is_host_bootstrap
                and node.module == "app.host"
            ):
                self._host_module_aliases.update(
                    alias.asname or alias.name for alias in node.names
                )
        self.generic_visit(node)

    @override
    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Reject module-qualified access to another host owner's private symbol."""
        dotted = _dotted_name(node)
        if (
            dotted is not None
            and self._is_host_owner
            and not self._is_host_bootstrap
            and node.attr.startswith("_")
            and (
                dotted.startswith("app.host.")
                or dotted.rsplit(".", maxsplit=1)[0] in self._host_module_aliases
            )
        ):
            self.violations.append(
                ArchitecturalViolation(
                    self.file_path,
                    node.lineno,
                    "ARCH-011-HOST-PRIVATE",
                    "Only host/bootstrap.py may access another owner's private "
                    "construction symbols.",
                )
            )
        self.generic_visit(node)

    @override
    def visit_Constant(self, node: ast.Constant) -> None:
        """Reject XML media types and transfer filenames."""
        if isinstance(node.value, str) and XML_LITERAL_PATTERN.search(repr(node.value)):
            self.violations.append(
                ArchitecturalViolation(
                    self.file_path,
                    node.lineno,
                    "ARCH-009-JSON-ONLY",
                    "HaruQuantAI-owned interchange must use versioned JSON, not XML.",
                )
            )
        self.generic_visit(node)


def check_file(py_file: Path) -> list[ArchitecturalViolation]:
    """Check one Python source file."""
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    except (OSError, SyntaxError) as error:
        return [
            ArchitecturalViolation(
                py_file,
                getattr(error, "lineno", 1) or 1,
                "ARCH-000-PARSE",
                str(error),
            )
        ]
    visitor = ArchitecturalVisitor(py_file)
    visitor.check_module(tree)
    visitor.visit(tree)
    return visitor.violations


def check_frontend_file(source_file: Path) -> list[ArchitecturalViolation]:
    """Check one frontend source file for XML interchange implementation."""
    try:
        lines = source_file.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        return [ArchitecturalViolation(source_file, 1, "ARCH-000-PARSE", str(error))]
    for line_number, line in enumerate(lines, start=1):
        if FRONTEND_XML_IMPLEMENTATION_PATTERN.search(
            line
        ) or XML_LITERAL_PATTERN.search(line):
            return [
                ArchitecturalViolation(
                    source_file,
                    line_number,
                    "ARCH-009-JSON-ONLY",
                    "Frontend interchange must use versioned JSON, not XML.",
                )
            ]
    return []


def _is_frontend_source(source_file: Path) -> bool:
    """Return whether a file is an active frontend source file."""
    return (
        source_file.suffix.lower() in FRONTEND_SOURCE_SUFFIXES
        and UI_SOURCE_ROOT in source_file.resolve().parents
    )


def _reset_boundary_violations() -> list[ArchitecturalViolation]:
    """Reject accidental restoration of superseded backend roots."""
    violations: list[ArchitecturalViolation] = []
    for name in sorted(FORBIDDEN_APP_ROOTS):
        path = APP_ROOT / name
        contains_source = path.is_file() or (path.is_dir() and any(path.rglob("*.py")))
        if contains_source:
            violations.append(
                ArchitecturalViolation(
                    path,
                    1,
                    "ARCH-010-RESET-BOUNDARY",
                    f"Superseded backend path must remain absent: app/{name}",
                )
            )
    return violations


def _current_topology_violations() -> list[ArchitecturalViolation]:
    """Require the exact source topology approved for S1."""
    violations: list[ArchitecturalViolation] = []
    roots = {
        path.name
        for path in APP_ROOT.iterdir()
        if path.is_file() or path.name == "ui" or any(path.rglob("*.py"))
    }
    if roots != CURRENT_APP_ROOTS:
        violations.append(
            ArchitecturalViolation(
                APP_ROOT,
                1,
                "ARCH-010-RESET-BOUNDARY",
                f"Unexpected application roots: {sorted(roots ^ CURRENT_APP_ROOTS)}",
            )
        )
    for directory, expected in (
        (APP_ROOT / "kernel", CURRENT_KERNEL_FILES),
        (APP_ROOT / "host", CURRENT_HOST_FILES),
        (APP_ROOT / "plugins", CURRENT_PLUGINS_FILES),
    ):
        actual = {path.name for path in directory.glob("*.py")}
        if actual != expected:
            violations.append(
                ArchitecturalViolation(
                    directory,
                    1,
                    "ARCH-012-STAGE-TOPOLOGY",
                    f"Unexpected source files: {sorted(actual ^ expected)}",
                )
            )
    for family_name, expected_files in sorted(CURRENT_PLUGIN_FAMILIES.items()):
        family_dir = APP_ROOT / "plugins" / family_name
        actual = {path.name for path in family_dir.glob("*.py")}
        expected_py = {f for f in expected_files if f.endswith(".py")}
        if actual != expected_py:
            violations.append(
                ArchitecturalViolation(
                    family_dir,
                    1,
                    "ARCH-012-STAGE-TOPOLOGY",
                    f"Unexpected source files in {family_name}: "
                    f"{sorted(actual ^ expected_py)}",
                )
            )
    return violations


def check_directory(directory: Path) -> list[ArchitecturalViolation]:
    """Check supported source files recursively under a directory."""
    violations: list[ArchitecturalViolation] = []
    if directory.resolve() == APP_ROOT.resolve():
        violations.extend(_reset_boundary_violations())
        violations.extend(_current_topology_violations())
    for source_file in directory.rglob("*"):
        if source_file.suffix == ".py":
            violations.extend(check_file(source_file))
        elif _is_frontend_source(source_file):
            violations.extend(check_frontend_file(source_file))
    return violations


def check_paths(paths: Sequence[str]) -> list[ArchitecturalViolation]:
    """Resolve and check application-relative paths."""
    violations: list[ArchitecturalViolation] = []
    for raw_path in paths:
        candidate = Path(raw_path)
        resolved = candidate if candidate.is_absolute() else REPO_ROOT / candidate
        resolved = resolved.resolve()
        if not resolved.exists() or not (
            resolved == APP_ROOT.resolve() or APP_ROOT.resolve() in resolved.parents
        ):
            raise ValueError(f"Path is outside app or missing: {raw_path}")
        if resolved.is_dir():
            violations.extend(check_directory(resolved))
        elif resolved.suffix == ".py":
            violations.extend(check_file(resolved))
        elif _is_frontend_source(resolved):
            violations.extend(check_frontend_file(resolved))
    return violations


def main(arguments: Sequence[str] | None = None) -> int:
    """Run architecture checks and return a process exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", default=[str(APP_ROOT)])
    args = parser.parse_args(arguments)
    try:
        violations = check_paths(args.paths)
    except ValueError as error:
        print(error)
        return 2
    for violation in violations:
        path = violation.file_path
        try:
            path = path.resolve().relative_to(REPO_ROOT)
        except ValueError:
            pass
        print(f"{path}:{violation.line_number}: {violation.rule}: {violation.message}")
    if violations:
        print(f"Architecture check failed with {len(violations)} violation(s).")
        return 1
    print("Architecture check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
