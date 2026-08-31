"""AST-based executable architecture constraint enforcer.

Traces to: P16-T01, Phase 16, Gate G16
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


class BoundaryViolation:
    """Represents a single detected architectural boundary violation."""

    def __init__(self, code: str, path: str, line: int, target: str) -> None:
        """Initialize boundary violation record."""
        self.code = code
        self.path = path.replace("\\", "/")
        self.line = line
        self.target = target

    def format(self) -> str:
        """Format violation into standardized one-line string.

        Returns:
            Formatted string representation.
        """
        return f"{self.code} {self.path}:{self.line} {self.target}"

    def sort_key(self) -> tuple[str, str, int, str]:
        """Return tuple key for deterministic sorting.

        Returns:
            Deterministic sorting key.
        """
        return (self.code, self.path, self.line, self.target)


def _check_import_node(
    node: ast.Import | ast.ImportFrom,
    rel_path: str,
    is_kernel: bool,
    is_cap: bool,
) -> list[BoundaryViolation]:
    """Check an import statement for kernel or spec boundaries.

    Returns:
        List of detected BoundaryViolation records.
    """
    violations: list[BoundaryViolation] = []
    targets: list[str] = []
    if isinstance(node, ast.Import):
        targets = [alias.name for alias in node.names]
    elif isinstance(node, ast.ImportFrom) and node.module:
        targets = [node.module]

    for target in targets:
        if is_kernel and target.startswith(("app.services", "app.agentic", "app.ui")):
            violations.append(
                BoundaryViolation(
                    "KERNEL_BUSINESS_IMPORT", rel_path, node.lineno, target
                )
            )
        if is_cap and ".providers" in target:
            violations.append(
                BoundaryViolation("SPEC_PROVIDER_IMPORT", rel_path, node.lineno, target)
            )
    return violations


def _check_call_node(
    node: ast.Call,
    rel_path: str,
    allowlist: set[str],
) -> list[BoundaryViolation]:
    """Check a function call for unallowlisted dynamic imports.

    Returns:
        List of detected BoundaryViolation records.
    """
    func_name = ""
    if isinstance(node.func, ast.Name):
        func_name = node.func.id
    elif isinstance(node.func, ast.Attribute):
        func_name = node.func.attr

    if func_name not in ("import_module", "__import__") or not node.args:
        return []

    first_arg = node.args[0]
    if not isinstance(first_arg, ast.Constant) or not isinstance(first_arg.value, str):
        return []

    imported_mod = first_arg.value
    root_pkg = imported_mod.split(".")[0]
    if (
        root_pkg in sys.stdlib_module_names
        or root_pkg in allowlist
        or imported_mod in allowlist
        or imported_mod.startswith(".")
        or rel_path.startswith("tests/")
    ):
        return []

    return [
        BoundaryViolation(
            "DYNAMIC_IMPORT_NOT_ALLOWLISTED",
            rel_path,
            node.lineno,
            imported_mod,
        )
    ]


def check_file_ast(
    file_path: Path,
    repo_root: Path,
    allowlist: set[str],
) -> list[BoundaryViolation]:
    """Analyze a single Python file AST for architecture boundary violations.

    Args:
        file_path: Path to Python source file.
        repo_root: Repository root path.
        allowlist: Set of allowlisted dynamic import module names.

    Returns:
        List of detected BoundaryViolation instances.
    """
    rel_path = str(file_path.relative_to(repo_root)).replace("\\", "/")
    violations: list[BoundaryViolation] = []

    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError, OSError:
        return violations

    is_kernel = rel_path.startswith("app/kernel/")
    is_cap = rel_path.startswith("app/contracts/")

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            violations.extend(_check_import_node(node, rel_path, is_kernel, is_cap))
        elif isinstance(node, ast.Call):
            violations.extend(_check_call_node(node, rel_path, allowlist))

    return violations


def run_boundary_check(
    root: Path,
    matrix_path: Path,
) -> list[BoundaryViolation]:
    """Execute complete architecture boundary scan across Python files.

    Args:
        root: Root directory to scan.
        matrix_path: Path to removability_matrix.json.

    Returns:
        List of all detected violations.
    """
    if not matrix_path.is_file():
        print(f"Matrix file not found: {matrix_path}", file=sys.stderr)
        sys.exit(2)

    try:
        matrix_data = json.loads(matrix_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Invalid matrix file: {exc}", file=sys.stderr)
        sys.exit(2)

    allowlist_entries = matrix_data.get("dynamic_import_allowlist", [])
    allowlist = {
        entry["module"]
        for entry in allowlist_entries
        if isinstance(entry, dict) and "module" in entry
    }

    violations: list[BoundaryViolation] = []
    for py_file in root.glob("app/**/*.py"):
        if "__pycache__" in py_file.parts:
            continue
        violations.extend(check_file_ast(py_file, root, allowlist))

    return sorted(violations, key=lambda v: v.sort_key())


def main() -> None:
    """CLI entry point for architecture boundary enforcement."""
    parser = argparse.ArgumentParser(
        description="Enforce provider and kernel architecture boundaries."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(),
        help="Root directory of repository.",
    )
    parser.add_argument(
        "--matrix",
        type=Path,
        required=True,
        help="Path to removability_matrix.json.",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    matrix = args.matrix.resolve()

    violations = run_boundary_check(root, matrix)

    if not violations:
        print("provider architecture: PASS")
        sys.exit(0)

    for v in violations:
        print(v.format())

    print(f"\nFAILURE: {len(violations)} architecture boundary violations found.")
    sys.exit(1)


if __name__ == "__main__":
    main()
