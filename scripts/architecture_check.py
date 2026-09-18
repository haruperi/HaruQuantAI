"""Static AST Architectural Rule Checker for HaruQuantAI.

Enforces universal modular monolith invariants across app/:
- ARCH-001-INIT-PURITY: __init__.py files must be docstring-only or empty.
- ARCH-002-MANAGED-TASKS: Direct asyncio.create_task() prohibited in services.
- ARCH-003-NO-LOGGING-BASICCONFIG: logging.basicConfig() prohibited in features.
- ARCH-004-KERNEL-PURITY: app/kernel must not import contracts or services.
- ARCH-005-CONTRACT-PURITY: app/contracts must not import services or runtime.
- ARCH-006-FEATURE-INDEPENDENCE: Service features must not import other features.
- ARCH-007-BOOTSTRAP-ISOLATION: Features and kernel must not import app.main/registry.
- ARCH-008-NO-COMPOSITION: app/composition is obsolete and prohibited.
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import override

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_ROOT = REPO_ROOT / "app"

DOMAIN_OFFSET = 1
FEATURE_OFFSET = 2
MIN_TARGET_PARTS = 4


@dataclass(frozen=True, slots=True)
class ArchitecturalViolation:
    """Represents a static architectural constraint violation."""

    file_path: Path
    line_number: int
    rule: str
    message: str


def _is_obsolete_composition_path(file_path: Path) -> bool:
    """Return whether source is inside the obsolete composition package."""
    parts = file_path.parts
    return any(
        part == "app" and parts[index + 1] == "composition"
        for index, part in enumerate(parts[:-1])
    )


class ArchitecturalVisitor(ast.NodeVisitor):
    """AST visitor enforcing strict architectural invariants across the codebase."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        if "app" in file_path.parts:
            app_idx = file_path.parts.index("app")
            self.app_parts = file_path.parts[app_idx:]
        else:
            self.app_parts = file_path.parts

        self.violations: list[ArchitecturalViolation] = []
        self._is_kernel = len(self.app_parts) > 1 and self.app_parts[1] == "kernel"
        self._is_service = len(self.app_parts) > 1 and self.app_parts[1] == "services"
        self._is_contract = len(self.app_parts) > 1 and self.app_parts[1] == "contracts"
        self._is_init = self.file_path.name == "__init__.py"

    def check_init_purity(self, node: ast.Module) -> None:
        """Rule 1: __init__.py files must only contain a docstring or be empty."""
        if not self._is_init:
            return

        body = node.body
        if not body:
            return

        if (
            len(body) == 1
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            return

        for stmt in body:
            if (
                stmt is body[0]
                and isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Constant)
                and isinstance(stmt.value.value, str)
            ):
                continue
            self.violations.append(
                ArchitecturalViolation(
                    file_path=self.file_path,
                    line_number=stmt.lineno,
                    rule="ARCH-001-INIT-PURITY",
                    message=(
                        "__init__.py must not contain executable code, assignments, "
                        f"or imports; found unexpected {type(stmt).__name__}."
                    ),
                )
            )

    @override
    def visit_Call(self, node: ast.Call) -> None:
        """Check forbidden function and method calls."""
        # Rule 2: asyncio.create_task() prohibited in services (use context.spawn)
        if (
            self._is_service
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "create_task"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "asyncio"
        ):
            self.violations.append(
                ArchitecturalViolation(
                    file_path=self.file_path,
                    line_number=node.lineno,
                    rule="ARCH-002-MANAGED-TASKS",
                    message=(
                        "Direct 'asyncio.create_task()' is prohibited outside "
                        "app/kernel. Use 'context.spawn()' instead."
                    ),
                )
            )

        # Rule 3: logging.basicConfig() prohibited in features
        if (
            (self._is_service or self._is_kernel or self._is_contract)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "basicConfig"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "logging"
        ):
            self.violations.append(
                ArchitecturalViolation(
                    file_path=self.file_path,
                    line_number=node.lineno,
                    rule="ARCH-003-NO-LOGGING-BASICCONFIG",
                    message=(
                        "Features must not call logging.basicConfig(). "
                        "Use 'from app.kernel.logging import get_logger'."
                    ),
                )
            )

        self.generic_visit(node)

    @override
    def visit_Import(self, node: ast.Import) -> None:
        """Check forbidden module-level imports."""
        for alias in node.names:
            self._check_import_target(alias.name, node.lineno)
        self.generic_visit(node)

    @override
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check forbidden from-imports."""
        if node.module:
            self._check_import_target(node.module, node.lineno)
        self.generic_visit(node)

    def _check_import_target(self, target_module: str, lineno: int) -> None:
        """Validate imported target against layer boundary rules."""
        # Rule 8: Obsolete composition
        if target_module == "app.composition" or target_module.startswith(
            "app.composition."
        ):
            self.violations.append(
                ArchitecturalViolation(
                    file_path=self.file_path,
                    line_number=lineno,
                    rule="ARCH-008-NO-COMPOSITION",
                    message=(
                        f"Import of '{target_module}' is prohibited. "
                        "app/composition is obsolete; use app/kernel."
                    ),
                )
            )

        # Rule 4: Kernel purity
        if self._is_kernel:
            if target_module.startswith(
                ("app.services", "app.contracts", "app.ui", "app.main", "app.registry")
            ):
                self.violations.append(
                    ArchitecturalViolation(
                        file_path=self.file_path,
                        line_number=lineno,
                        rule="ARCH-004-KERNEL-PURITY",
                        message=(
                            "Kernel must not import application module "
                            f"'{target_module}'."
                        ),
                    )
                )

        # Rule 5: Contract purity
        if self._is_contract:
            if target_module.startswith(
                ("app.services", "app.ui", "app.main", "app.registry")
            ):
                self.violations.append(
                    ArchitecturalViolation(
                        file_path=self.file_path,
                        line_number=lineno,
                        rule="ARCH-005-CONTRACT-PURITY",
                        message=(
                            "Contract must not import service or runtime module "
                            f"'{target_module}'."
                        ),
                    )
                )
            elif target_module.startswith(
                "app.kernel"
            ) and not target_module.startswith("app.kernel.capability"):
                self.violations.append(
                    ArchitecturalViolation(
                        file_path=self.file_path,
                        line_number=lineno,
                        rule="ARCH-005-CONTRACT-PURITY",
                        message=(
                            "Contract must not import kernel runtime module "
                            f"'{target_module}'. Only app.kernel.capability is allowed."
                        ),
                    )
                )

        # Rule 7: Bootstrap isolation
        if (
            self._is_service or self._is_contract or self._is_kernel
        ) and target_module in ("app.main", "app.registry"):
            self.violations.append(
                ArchitecturalViolation(
                    file_path=self.file_path,
                    line_number=lineno,
                    rule="ARCH-007-BOOTSTRAP-ISOLATION",
                    message=(
                        f"Module must not import bootstrap module '{target_module}'. "
                        "Bootstrap composes features; features do not depend on it."
                    ),
                )
            )

        # Rule 6: Cross-feature independence in app/services/<domain>/<feature>.py
        if (
            self._is_service
            and not self.file_path.name.endswith(("_usage.py", "example.py"))
            and target_module.startswith("app.services.")
            and "services" in self.app_parts
        ):
            srv_idx = self.app_parts.index("services")
            if len(self.app_parts) > srv_idx + FEATURE_OFFSET:
                source_domain = self.app_parts[srv_idx + DOMAIN_OFFSET]
                source_feature = self.app_parts[srv_idx + FEATURE_OFFSET].removesuffix(
                    ".py"
                )
                target_parts = target_module.split(".")
                if len(target_parts) >= MIN_TARGET_PARTS:
                    target_domain = target_parts[2]
                    target_feature = target_parts[3]

                    # Dedicated domain persistence is permitted for its own domain
                    if target_domain == "persistence" and (
                        len(target_parts) == 3 or target_feature == source_domain
                    ):
                        return

                    if (source_domain, source_feature) != (
                        target_domain,
                        target_feature,
                    ):
                        self.violations.append(
                            ArchitecturalViolation(
                                file_path=self.file_path,
                                line_number=lineno,
                                rule="ARCH-006-FEATURE-INDEPENDENCE",
                                message=(
                                    f"Feature '{source_domain}/{source_feature}' "
                                    f"imports '{target_domain}/{target_feature}'. "
                                    "Features must collaborate via contracts."
                                ),
                            )
                        )


def check_file(py_file: Path) -> list[ArchitecturalViolation]:
    """Scan one Python file for architectural violations."""
    violations: list[ArchitecturalViolation] = []
    if _is_obsolete_composition_path(py_file):
        violations.append(
            ArchitecturalViolation(
                file_path=py_file,
                line_number=1,
                rule="ARCH-008-NO-COMPOSITION",
                message=(
                    "app/composition is obsolete. "
                    "Use business-neutral primitives from app/kernel."
                ),
            )
        )

    try:
        content = py_file.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(py_file))
        visitor = ArchitecturalVisitor(py_file)
        visitor.check_init_purity(tree)
        visitor.visit(tree)
        violations.extend(visitor.violations)
    except SyntaxError as error:
        violations.append(
            ArchitecturalViolation(
                file_path=py_file,
                line_number=error.lineno or 1,
                rule="SYNTAX-ERROR",
                message=str(error),
            )
        )
    return violations


def check_directory(directory: Path) -> list[ArchitecturalViolation]:
    """Scan all python files in directory for architectural violations."""
    violations: list[ArchitecturalViolation] = []
    for py_file in directory.rglob("*.py"):
        violations.extend(check_file(py_file))
    return violations


def check_paths(paths: Sequence[str]) -> list[ArchitecturalViolation]:
    """Validate and scan explicit application paths."""
    violations: list[ArchitecturalViolation] = []
    for value in paths:
        candidate = Path(value)
        resolved = (
            candidate.resolve()
            if candidate.is_absolute()
            else (REPO_ROOT / candidate).resolve()
        )
        if not resolved.is_relative_to(APP_ROOT.resolve()) or not resolved.exists():
            message = f"Architecture target is outside app or missing: {value}"
            raise ValueError(message)
        if resolved.is_dir():
            violations.extend(check_directory(resolved))
        elif resolved.suffix == ".py":
            violations.extend(check_file(resolved))
        else:
            message = f"Architecture target is not Python source: {value}"
            raise ValueError(message)
    return violations


def main(arguments: Sequence[str] | None = None) -> int:
    """Run architectural check across the application source tree."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*")
    options = parser.parse_args(arguments)
    targets = options.paths or [str(APP_ROOT)]

    print("========================================")
    print("Running Architectural AST Invariant Check...")
    print(f"Scanning targets: {', '.join(targets)}")
    print("========================================")

    try:
        violations = check_paths(targets)
    except ValueError as error:
        print(f"[FAILURE] {error}")
        return 2

    if not violations:
        print("[SUCCESS] All architectural rules passed without violations!")
        return 0

    print(f"\n[FAILURE] Found {len(violations)} architectural violations:\n")
    for v in violations:
        print(f"  [{v.rule}] {v.file_path}:{v.line_number}")
        print(f"    -> {v.message}\n")

    return 1


if __name__ == "__main__":
    sys.exit(main())
