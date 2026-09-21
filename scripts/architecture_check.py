"""Check the architecture invariants of the retained kernel/UI baseline."""

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
FORBIDDEN_APP_ROOTS = frozenset({"contracts", "services", "registry.py", "main.py"})
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


class ArchitecturalVisitor(ast.NodeVisitor):
    """Enforce Python invariants retained during the backend reset."""

    def __init__(self, file_path: Path) -> None:
        """Initialize the visitor for one source file."""
        self.file_path = file_path
        parts = _app_parts(file_path)
        self._is_kernel = len(parts) > 1 and parts[1] == "kernel"
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

    def _check_import(self, target: str, line_number: int) -> None:
        """Check kernel purity and XML interchange imports."""
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

    @override
    def visit_Import(self, node: ast.Import) -> None:
        """Check every direct import."""
        for alias in node.names:
            self._check_import(alias.name, node.lineno)
        self.generic_visit(node)

    @override
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check every from-import."""
        if node.level:
            if self._is_kernel:
                self.violations.append(
                    ArchitecturalViolation(
                        self.file_path,
                        node.lineno,
                        "ARCH-004-KERNEL-PURITY",
                        "Kernel source must use absolute imports.",
                    )
                )
        else:
            self._check_import(node.module or "", node.lineno)
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


def check_directory(directory: Path) -> list[ArchitecturalViolation]:
    """Check supported source files recursively under a directory."""
    violations: list[ArchitecturalViolation] = []
    if directory.resolve() == APP_ROOT.resolve():
        violations.extend(_reset_boundary_violations())
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
