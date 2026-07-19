"""Safe parameter-space validation and expression evaluation."""

from __future__ import annotations

import ast
import operator
from collections.abc import Mapping, Sequence

from app.services.optimization.parameters.contracts import (
    ParameterKind,
    ParameterSpace,
    ParameterValue,
)
from app.utils import logger

_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}
_COMPARISON_OPERATORS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda left, right: left in right,
    ast.NotIn: lambda left, right: left not in right,
}


def _parse(expression: str, names: set[str]) -> ast.Expression:
    """Parse and validate one restricted expression.

    Args:
        expression: Constraint or activation expression.
        names: Approved parameter names.

    Returns:
        Validated expression tree.

    Raises:
        ValueError: If syntax or a referenced name is unsafe.
    """
    logger.debug("Parsing restricted Optimization expression")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as error:
        raise ValueError("parameter expression syntax is invalid") from error
    allowed = (
        ast.Expression,
        ast.BoolOp,
        ast.And,
        ast.Or,
        ast.UnaryOp,
        ast.Not,
        ast.USub,
        ast.UAdd,
        ast.BinOp,
        *tuple(_BINARY_OPERATORS),
        ast.Compare,
        *tuple(_COMPARISON_OPERATORS),
        ast.Name,
        ast.Load,
        ast.Constant,
        ast.Tuple,
        ast.List,
    )
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            raise ValueError(  # noqa: TRY004
                "parameter expression contains unsafe syntax"
            )
        if isinstance(node, ast.Name) and node.id not in names:
            raise ValueError("parameter expression references an unknown name")
        if isinstance(node, ast.Constant) and not isinstance(
            node.value, (bool, int, str, type(None))
        ):
            raise ValueError(  # noqa: TRY004
                "parameter expression constant is unsupported"
            )
    return tree


def _evaluate(node: ast.AST, values: Mapping[str, object]) -> object:  # noqa: C901, PLR0911, PLR0912
    """Evaluate one validated AST node recursively.

    Args:
        node: Validated AST node.
        values: Parameter value mapping.

    Returns:
        Evaluated scalar, collection, or boolean.

    Raises:
        ValueError: If runtime values or operations are invalid.
    """
    logger.debug("Evaluating restricted Optimization expression node")
    if isinstance(node, ast.Expression):
        return _evaluate(node.body, values)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id not in values:
            raise ValueError("parameter expression value is missing")
        return values[node.id]
    if isinstance(node, (ast.Tuple, ast.List)):
        return tuple(_evaluate(item, values) for item in node.elts)
    if isinstance(node, ast.UnaryOp):
        operand = _evaluate(node.operand, values)
        if isinstance(node.op, ast.Not):
            return not bool(operand)
        if isinstance(node.op, ast.USub):
            return -operand  # type: ignore[operator]
        return +operand  # type: ignore[operator]
    if isinstance(node, ast.BinOp):
        operation = _BINARY_OPERATORS.get(type(node.op))
        if operation is None:
            raise ValueError("binary operator is not allowed")
        try:
            return operation(
                _evaluate(node.left, values), _evaluate(node.right, values)
            )
        except (ArithmeticError, TypeError) as error:
            raise ValueError("parameter arithmetic is invalid") from error
    if isinstance(node, ast.BoolOp):
        results = (_evaluate(item, values) for item in node.values)
        return (
            all(bool(item) for item in results)
            if isinstance(node.op, ast.And)
            else any(bool(item) for item in results)
        )
    if isinstance(node, ast.Compare):
        left = _evaluate(node.left, values)
        for operation_node, comparator in zip(node.ops, node.comparators, strict=True):
            right = _evaluate(comparator, values)
            operation = _COMPARISON_OPERATORS.get(type(operation_node))
            if operation is None:
                raise ValueError("comparison operator is not allowed")
            try:
                if not operation(left, right):
                    return False
            except TypeError as error:
                raise ValueError("parameter comparison is invalid") from error
            left = right
        return True
    raise ValueError("parameter expression node is unsupported")


def _expression_names(expression: str, names: set[str]) -> set[str]:
    """Return referenced names from a validated expression.

    Args:
        expression: Expression text.
        names: Approved parameter names.

    Returns:
        Referenced parameter names.
    """
    logger.debug("Collecting Optimization expression dependencies")
    tree = _parse(expression, names)
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}


def _cardinality(space: ParameterSpace) -> int:
    """Calculate the maximum candidate expansion.

    Args:
        space: Parameter space definition.

    Returns:
        Product of all possible parameter values.

    Raises:
        ValueError: If a numeric contract is unexpectedly incomplete.
    """
    logger.debug("Calculating Optimization parameter-space cardinality")
    total = 1
    for item in space.parameters:
        if item.kind in {ParameterKind.INTEGER, ParameterKind.FLOAT}:
            if item.minimum is None or item.maximum is None or item.step is None:
                raise ValueError("numeric range is incomplete")
            total *= int((item.maximum - item.minimum) // item.step) + 1
        elif item.kind is ParameterKind.CATEGORICAL:
            total *= len(item.choices)
        elif item.kind is ParameterKind.BOOLEAN:
            total *= 2
    return total


def validate_parameter_space(
    space: ParameterSpace,
    *,
    max_expansion: int,
    max_constraints: int,
) -> None:
    """Validate expressions, activation cycles, and resource bounds.

    Args:
        space: Parameter space to validate.
        max_expansion: Positive maximum candidate count.
        max_constraints: Positive maximum constraint count.

    Raises:
        ValueError: If syntax, dependencies, or limits are invalid.
    """
    logger.info("Validating bounded Optimization parameter space")
    if max_expansion <= 0 or max_constraints <= 0:
        raise ValueError("parameter-space limits must be positive")
    if len(space.constraints) > max_constraints:
        raise ValueError("parameter constraint count exceeds the limit")
    if _cardinality(space) > max_expansion:
        raise ValueError("parameter-space expansion exceeds the limit")
    names = {item.name for item in space.parameters}
    for expression in space.constraints:
        _parse(expression, names)
    graph = {
        item.name: (
            _expression_names(item.active_when, names)
            if item.active_when is not None
            else set()
        )
        for item in space.parameters
    }

    def visit(name: str, visiting: set[str], visited: set[str]) -> None:
        """Visit one activation dependency for cycle detection.

        Args:
            name: Current parameter name.
            visiting: Active traversal path.
            visited: Fully validated parameter names.

        Raises:
            ValueError: If an activation cycle exists.
        """
        logger.debug("Checking activation dependency for %s", name)
        if name in visiting:
            raise ValueError("conditional parameter dependencies are cyclic")
        if name in visited:
            return
        visiting.add(name)
        for dependency in graph[name]:
            visit(dependency, visiting, visited)
        visiting.remove(name)
        visited.add(name)

    visited: set[str] = set()
    for name in names:
        visit(name, set(), visited)


def evaluate_constraints(
    parameters: Mapping[str, object], constraints: Sequence[str]
) -> bool:
    """Evaluate validated constraint expressions against supplied parameters.

    Args:
        parameters: Complete parameter values.
        constraints: Constraint expressions.

    Returns:
        True only when every constraint evaluates true.

    Raises:
        ValueError: If an expression is unsafe or cannot be evaluated.
    """
    logger.info("Evaluating Optimization parameter constraints")
    names = set(parameters)
    return all(bool(_evaluate(_parse(item, names), parameters)) for item in constraints)


def get_executable_parameters(
    parameters: Mapping[str, ParameterValue], space: ParameterSpace
) -> dict[str, ParameterValue]:
    """Remove inactive parameters from an execution candidate.

    Args:
        parameters: Candidate values keyed by parameter name.
        space: Source parameter-space definition.

    Returns:
        New mapping containing only active parameters.

    Raises:
        ValueError: If candidate values are incomplete or contain unknown names.
    """
    logger.info("Selecting executable Optimization parameters")
    expected = {item.name for item in space.parameters}
    if set(parameters) != expected:
        raise ValueError("candidate parameters must exactly match the parameter space")
    executable: dict[str, ParameterValue] = {}
    for item in space.parameters:
        if item.active_when is None or bool(
            _evaluate(_parse(item.active_when, expected), parameters)
        ):
            executable[item.name] = parameters[item.name]
    return executable


__all__ = [
    "evaluate_constraints",
    "get_executable_parameters",
    "validate_parameter_space",
]
