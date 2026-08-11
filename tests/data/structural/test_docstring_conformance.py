"""Google-style docstring conformance for Data production code."""

from __future__ import annotations

import ast
from pathlib import Path

_DATA_ROOT = Path("app/services/data")
_SECTION_HEADERS = {"Args:", "Returns:", "Raises:", "Yields:"}


def _function_body(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.stmt]:
    """Return statements after the function docstring, when present."""
    body = list(node.body)
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
    ):
        body = body[1:]
    return body


def _walk_local_body(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[ast.AST, ...]:
    """Walk a callable without attributing nested callable behavior to it."""
    found: list[ast.AST] = []

    def visit(current: ast.AST) -> None:
        if current is not node and isinstance(
            current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
        ):
            return
        found.append(current)
        for child in ast.iter_child_nodes(current):
            visit(child)

    for statement in _function_body(node):
        visit(statement)
    return tuple(found)


def _parameters(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[str, ...]:
    """Return explicitly documentable parameter names for one callable."""
    arguments = node.args
    names = [
        argument.arg
        for argument in (*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs)
        if argument.arg not in {"self", "cls"}
    ]
    if arguments.vararg is not None:
        names.append(arguments.vararg.arg)
    if arguments.kwarg is not None:
        names.append(arguments.kwarg.arg)
    return tuple(names)


def _has_value_return(nodes: tuple[ast.AST, ...]) -> bool:
    """Return whether a callable explicitly returns a non-None value."""
    return any(
        isinstance(item, ast.Return)
        and item.value is not None
        and not (isinstance(item.value, ast.Constant) and item.value.value is None)
        for item in nodes
    )


def _has_yield(nodes: tuple[ast.AST, ...]) -> bool:
    """Return whether a callable is a generator."""
    return any(isinstance(item, (ast.Yield, ast.YieldFrom)) for item in nodes)


def _documented_parameter_names(docstring: str) -> set[str]:
    """Extract parameter names from a Google-style Args section."""
    lines = docstring.splitlines()
    documented: set[str] = set()
    in_args = False
    for line in lines:
        stripped = line.strip()
        if stripped == "Args:":
            in_args = True
            continue
        if in_args and stripped in _SECTION_HEADERS:
            break
        if in_args and stripped and not line.startswith((" ", "\t")):
            break
        if in_args and ":" in stripped:
            documented.add(stripped.split(":", maxsplit=1)[0].lstrip("*").strip())
    return documented


def _callable_docstring_failures(
    path: Path,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    docstring: str,
) -> tuple[str, ...]:
    """Return applicable section failures for one callable."""
    location = f"{path}:{node.lineno} callable {node.name}"
    failures: list[str] = []
    parameters = _parameters(node)
    if parameters and "Args:" not in docstring:
        failures.append(f"{location}: missing Args section")
    elif parameters:
        missing = set(parameters) - _documented_parameter_names(docstring)
        if missing:
            failures.append(f"{location}: undocumented parameters {sorted(missing)}")

    local_nodes = _walk_local_body(node)
    if _has_yield(local_nodes) and "Yields:" not in docstring:
        failures.append(f"{location}: missing Yields section")
    elif _has_value_return(local_nodes) and "Returns:" not in docstring:
        failures.append(f"{location}: missing Returns section")
    if any(isinstance(item, ast.Raise) for item in local_nodes) and (
        "Raises:" not in docstring
    ):
        failures.append(f"{location}: missing Raises section")
    return tuple(failures)


def _docstring_failures(path: Path) -> tuple[str, ...]:
    """Return precise conformance failures for one production module."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    failures: list[str] = []
    if not ast.get_docstring(tree, clean=False):
        failures.append(f"{path}:1 module: missing description")

    for node in ast.walk(tree):
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        kind = "class" if isinstance(node, ast.ClassDef) else "callable"
        docstring = ast.get_docstring(node, clean=False)
        location = f"{path}:{node.lineno} {kind} {node.name}"
        if not docstring or not docstring.strip():
            failures.append(f"{location}: missing description")
            continue
        if not isinstance(node, ast.ClassDef):
            failures.extend(_callable_docstring_failures(path, node, docstring))
    return tuple(failures)


def test_all_data_production_docstrings_are_google_style() -> None:
    """Require applicable Google sections throughout Data production code."""
    failures = tuple(
        failure
        for path in sorted(_DATA_ROOT.rglob("*.py"))
        if "__pycache__" not in path.parts
        for failure in _docstring_failures(path)
    )
    assert not failures, "\n" + "\n".join(failures)
