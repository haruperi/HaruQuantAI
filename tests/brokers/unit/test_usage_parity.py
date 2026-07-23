"""Verify 1:1 parity between FR IDs, usage functions, and main() reachability."""

import ast
import pathlib
import re

USAGE_DIR = pathlib.Path("tests/brokers/usage")


def test_usage_parity_and_reachability() -> None:  # noqa: C901
    """Verify that every FR-BRK-001..135 ID maps 1:1 to a reachable usage function."""
    usage_files = sorted(USAGE_DIR.glob("[0-9][0-9]_*.py"))
    assert len(usage_files) == 16

    all_fr_functions: dict[str, str] = {}
    deep_imports: list[str] = []

    for file_path in usage_files:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))

        # Check imports in usage file
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith("app.services.brokers.")
                and node.module != "app.services.brokers.testing"
            ):
                deep_imports.append(
                    f"{file_path.name}:{node.lineno} imports {node.module}"
                )

        # Find all fr_brokers_NNN functions
        fr_funcs_in_file: list[str] = []
        main_calls: set[str] = set()

        for stmt in tree.body:
            if isinstance(stmt, ast.FunctionDef):
                if stmt.name.startswith("fr_brokers_"):
                    fr_funcs_in_file.append(stmt.name)
                    # Extract FR ID from func name
                    m = re.match(r"fr_brokers_(\d{3})", stmt.name)
                    assert m is not None, (
                        f"Invalid function name {stmt.name} in {file_path.name}"
                    )
                    fr_id = f"FR-BRK-{m.group(1)}"
                    assert fr_id not in all_fr_functions, (
                        f"Duplicate FR function {fr_id} in {file_path.name}"
                    )
                    all_fr_functions[fr_id] = file_path.name
                elif stmt.name == "main":
                    for main_stmt in ast.walk(stmt):
                        if isinstance(main_stmt, ast.Call) and isinstance(
                            main_stmt.func, ast.Name
                        ):
                            main_calls.add(main_stmt.func.id)

        # Check reachability in main()
        for func in fr_funcs_in_file:
            assert func in main_calls, (
                f"Function {func} in {file_path.name} is not called in main()"
            )

    assert not deep_imports, (
        f"Prohibited deep imports found in usage files: {deep_imports}"
    )

    # Verify all 135 FRs are present
    expected_frs = {f"FR-BRK-{i:03d}" for i in range(1, 136)}
    missing = expected_frs - set(all_fr_functions.keys())
    assert not missing, f"Missing FR functions: {sorted(missing)}"
    assert len(all_fr_functions) == 135
