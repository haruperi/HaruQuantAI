"""Structural documentation checks for Stage 2 Utils source definitions."""

import ast
from pathlib import Path

_UTILS_ROOT = Path(__file__).resolve().parents[3] / "app" / "utils"


def _definitions(tree: ast.AST) -> list[ast.ClassDef | ast.FunctionDef]:
    """Return every class and synchronous function in an abstract syntax tree.

    Args:
        tree: Parsed Python module tree.

    Returns:
        Definitions in deterministic source order, including nested functions.
    """
    return sorted(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef | ast.FunctionDef)
        ),
        key=lambda node: (node.lineno, node.col_offset),
    )


def _documented_parameters(function: ast.FunctionDef) -> tuple[str, ...]:
    """Return parameter names that require caller-facing documentation.

    Args:
        function: Function definition being audited.

    Returns:
        Positional, keyword-only, variadic, and mapping parameter names except
        conventional ``self`` and ``cls`` receivers.
    """
    parameters = [
        *function.args.posonlyargs,
        *function.args.args,
        *function.args.kwonlyargs,
    ]
    names = [
        argument.arg for argument in parameters if argument.arg not in {"self", "cls"}
    ]
    if function.args.vararg is not None:
        names.append(function.args.vararg.arg)
    if function.args.kwarg is not None:
        names.append(function.args.kwarg.arg)
    return tuple(names)


def _returns_value(function: ast.FunctionDef) -> bool:
    """Return whether a function declares a non-``None`` return value.

    Args:
        function: Function definition being audited.

    Returns:
        ``True`` when the return annotation exists and is not ``None``.
    """
    annotation = function.returns
    return annotation is not None and not (
        isinstance(annotation, ast.Constant) and annotation.value is None
    )


def _raises_directly(function: ast.FunctionDef) -> bool:
    """Return whether a function body directly contains a raise statement.

    Nested function and class bodies are excluded because they own their own
    documentation contract.

    Args:
        function: Function definition being audited.

    Returns:
        ``True`` when the function itself contains at least one ``raise``.
    """
    pending: list[ast.AST] = list(function.body)
    while pending:
        node = pending.pop()
        if isinstance(node, ast.Raise):
            return True
        if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        pending.extend(ast.iter_child_nodes(node))
    return False


def _public_annotated_attributes(class_definition: ast.ClassDef) -> tuple[str, ...]:
    """Return public class-body attributes requiring an ``Attributes`` section.

    Args:
        class_definition: Class definition being audited.

    Returns:
        Public annotated attribute names in declaration order.
    """
    return tuple(
        statement.target.id
        for statement in class_definition.body
        if isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
        and not statement.target.id.startswith("_")
    )


def _class_docstring_failures(
    definition: ast.ClassDef,
    docstring: str,
    location: str,
) -> list[str]:
    """Return semantic documentation failures for one class.

    Args:
        definition: Class definition being audited.
        docstring: Cleaned non-empty class docstring.
        location: Repository-relative source location.

    Returns:
        Failures for missing public attribute documentation.
    """
    failures: list[str] = []
    attributes = _public_annotated_attributes(definition)
    if attributes and "Attributes:" not in docstring:
        failures.append(f"{location} {definition.name}: missing Attributes section")
    for attribute in attributes:
        if f"{attribute}:" not in docstring:
            failures.append(
                f"{location} {definition.name}: undocumented attribute {attribute}"
            )
    return failures


def _function_docstring_failures(
    definition: ast.FunctionDef,
    docstring: str,
    location: str,
) -> list[str]:
    """Return semantic documentation failures for one function.

    Args:
        definition: Function definition being audited.
        docstring: Cleaned non-empty function docstring.
        location: Repository-relative source location.

    Returns:
        Failures for undocumented inputs, output, or raised errors.
    """
    failures: list[str] = []
    parameters = _documented_parameters(definition)
    if parameters and "Args:" not in docstring:
        failures.append(f"{location} {definition.name}: missing Args section")
    for parameter in parameters:
        if f"{parameter}:" not in docstring:
            failures.append(
                f"{location} {definition.name}: undocumented parameter {parameter}"
            )
    if _returns_value(definition) and "Returns:" not in docstring:
        failures.append(f"{location} {definition.name}: missing Returns section")
    if _raises_directly(definition) and "Raises:" not in docstring:
        failures.append(f"{location} {definition.name}: missing Raises section")
    return failures


def test_utils_definitions_have_google_style_semantic_docstrings() -> None:
    """Require usable Google-style documentation for every Utils definition."""
    failures: list[str] = []
    for path in sorted(_UTILS_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for definition in _definitions(tree):
            location = (
                f"{path.relative_to(_UTILS_ROOT.parent.parent)}:{definition.lineno}"
            )
            docstring = ast.get_docstring(definition, clean=True)
            if not docstring:
                failures.append(f"{location} {definition.name}: missing docstring")
                continue
            if isinstance(definition, ast.ClassDef):
                failures.extend(
                    _class_docstring_failures(definition, docstring, location)
                )
            else:
                failures.extend(
                    _function_docstring_failures(definition, docstring, location)
                )
    assert not failures, "\n" + "\n".join(failures)
