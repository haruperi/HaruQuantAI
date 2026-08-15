"""Verify usage-program structure, main() reachability, and import boundaries."""

import ast
import pathlib

USAGE_DIR = pathlib.Path("tests/brokers/usage/features")


def test_usage_parity_and_reachability() -> None:  # noqa: C901
    """Verify 13 feature programs, reachable evidence functions, root-only imports.

    The Brokers README cites usage evidence at file level (one standalone program
    per registered feature), so parity is structural: exactly thirteen numbered
    programs, each with evidence functions reachable from ``main()`` behind a
    standalone-execution guard, and no deep Brokers imports.
    """
    usage_files = sorted(USAGE_DIR.glob("[0-9][0-9]_*.py"))
    assert len(usage_files) == 13

    deep_imports: list[str] = []

    for file_path in usage_files:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))

        # Usage programs import only the public root boundary (testing excepted).
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith("app.services.brokers.")
                and node.module != "app.services.brokers.conformance"
            ):
                deep_imports.append(
                    f"{file_path.name}:{node.lineno} imports {node.module}"
                )

        fr_funcs_in_file: list[str] = []
        calls_by_function: dict[str, set[str]] = {}
        has_main = False
        has_name_guard = False

        for stmt in tree.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                calls_by_function[stmt.name] = {
                    call.func.id
                    for call in ast.walk(stmt)
                    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                }
                if stmt.name.startswith(("fr_brokers_", "fr_brk_")):
                    fr_funcs_in_file.append(stmt.name)
                if stmt.name == "main":
                    has_main = True
            if (
                isinstance(stmt, ast.If)
                and isinstance(stmt.test, ast.Compare)
                and isinstance(stmt.test.left, ast.Name)
                and stmt.test.left.id == "__name__"
            ):
                has_name_guard = True

        assert has_main, f"{file_path.name} does not define main()"
        assert has_name_guard, (
            f"{file_path.name} lacks an if __name__ == '__main__' guard"
        )
        assert fr_funcs_in_file, f"{file_path.name} defines no fr_* evidence functions"

        # Check transitive reachability from main(), including async `_run`.
        reachable: set[str] = set()
        pending = ["main"]
        while pending:
            function_name = pending.pop()
            for called in calls_by_function.get(function_name, set()):
                if called not in reachable:
                    reachable.add(called)
                    pending.append(called)
        for func in fr_funcs_in_file:
            assert func in reachable, (
                f"Function {func} in {file_path.name} is not called in main()"
            )

    assert not deep_imports, (
        f"Prohibited deep imports found in usage files: {deep_imports}"
    )
