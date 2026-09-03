"""Static AST Architectural Rule Checker for HaruQuantAI."""

import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import override

APP_ROOT = Path(__file__).resolve().parent.parent / "app"
MIN_TARGET_PARTS = 4
DOMAIN_OFFSET = 1
FEATURE_OFFSET = 2


@dataclass(frozen=True, slots=True)
class ArchitecturalViolation:
    """Represents a static architectural constraint violation."""

    file_path: Path
    line_number: int
    rule: str
    message: str


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

        active_roots = {"kernel", "composition", "contracts"}
        active_services = {"workspace", "catalogue", "plugins", "brokers", "data"}
        min_service_parts = 3
        is_active = (len(self.app_parts) > 1 and self.app_parts[1] in active_roots) or (
            len(self.app_parts) >= min_service_parts
            and self.app_parts[1] == "services"
            and self.app_parts[2] in active_services
        )

        if not is_active:
            return

        for stmt in node.body:
            if (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Constant)
                and isinstance(stmt.value.value, str)
            ):
                continue
            if (
                isinstance(stmt, ast.AnnAssign)
                and isinstance(stmt.target, ast.Name)
                and stmt.target.id == "__all__"
            ):
                continue
            if isinstance(stmt, ast.Assign) and all(
                isinstance(t, ast.Name) and t.id == "__all__" for t in stmt.targets
            ):
                continue
            self.violations.append(
                ArchitecturalViolation(
                    file_path=self.file_path,
                    line_number=stmt.lineno,
                    rule="ARCH-001-INIT-PURITY",
                    message=(
                        f"__init__.py must not contain executable code, "
                        f"found {type(stmt).__name__}."
                    ),
                )
            )

    @override
    def visit_Call(self, node: ast.Call) -> None:
        """Check forbidden function and method calls."""
        # Rule 2: asyncio.create_task() only allowed inside app/kernel/
        active_migrated_domains = {
            "workspace",
            "catalogue",
            "plugins",
            "brokers",
            "data",
        }
        min_service_parts = 3
        is_active_service = (
            self._is_service
            and len(self.app_parts) >= min_service_parts
            and self.app_parts[2] in active_migrated_domains
        )
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "create_task"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "asyncio"
            and is_active_service
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
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "basicConfig"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "logging"
            and self._is_service
        ):
            self.violations.append(
                ArchitecturalViolation(
                    file_path=self.file_path,
                    line_number=node.lineno,
                    rule="ARCH-003-NO-LOGGING-BASICCONFIG",
                    message="Service features must not call logging.basicConfig().",
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
        # Rule 4: Contracts must never import service implementations.
        if self._is_contract and target_module.startswith("app.services"):
            self.violations.append(
                ArchitecturalViolation(
                    file_path=self.file_path,
                    line_number=lineno,
                    rule="ARCH-004-CONTRACT-PURITY",
                    message=f"Contract must not import '{target_module}'.",
                )
            )

        # Rule 6: Cross-service feature independence (excludes _usage.py)
        if (
            self._is_service
            and not self.file_path.name.endswith("_usage.py")
            and target_module.startswith("app.services.")
            and "services" in self.app_parts
        ):
            srv_idx = self.app_parts.index("services")
            if len(self.app_parts) > srv_idx + FEATURE_OFFSET:
                source_domain = self.app_parts[srv_idx + DOMAIN_OFFSET]
                active_migrated_domains = {
                    "workspace",
                    "catalogue",
                    "plugins",
                    "brokers",
                    "data",
                }
                if source_domain in active_migrated_domains:
                    source_feature = self.app_parts[srv_idx + FEATURE_OFFSET]
                    target_parts = target_module.split(".")
                    if len(target_parts) >= MIN_TARGET_PARTS:
                        target_domain = target_parts[2]
                        target_feature = target_parts[3]
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
                                        f"Feature '{source_domain}/"
                                        f"{source_feature}' cannot import "
                                        f"'{target_domain}/{target_feature}'."
                                    ),
                                )
                            )


def check_directory(directory: Path) -> list[ArchitecturalViolation]:
    """Scan all python files in directory for architectural violations.

    Args:
        directory: Root path to scan.

    Returns:
        List of detected ArchitecturalViolation instances.
    """
    violations: list[ArchitecturalViolation] = []
    for py_file in directory.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(py_file))
            visitor = ArchitecturalVisitor(py_file)
            visitor.check_init_purity(tree)
            visitor.visit(tree)
            violations.extend(visitor.violations)
        except SyntaxError as e:
            violations.append(
                ArchitecturalViolation(
                    file_path=py_file,
                    line_number=e.lineno or 1,
                    rule="SYNTAX-ERROR",
                    message=str(e),
                )
            )
    return violations


def main() -> int:
    """Run architectural check across the application source tree.

    Returns:
        0 if clean, 1 if violations found.
    """
    print("========================================")
    print("Running Architectural AST Invariant Check...")
    print(f"Scanning directory: {APP_ROOT}")
    print("========================================")

    violations = check_directory(APP_ROOT)

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
