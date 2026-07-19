"""Lazy bounded grid candidate generation."""

from __future__ import annotations

import itertools
from collections.abc import Iterator

from app.services.optimization.parameters import (
    ParameterKind,
    ParameterRange,
    ParameterSpace,
    ParameterValue,
    evaluate_constraints,
    get_executable_parameters,
    validate_parameter_space,
)
from app.utils import canonical_json, logger


def _values(item: ParameterRange) -> tuple[ParameterValue, ...]:
    """Expand one already-validated bounded range.

    Args:
        item: Parameter range.

    Returns:
        Ordered possible values.

    Raises:
        ValueError: If a numeric contract is unexpectedly incomplete.
    """
    logger.debug("Expanding one Optimization parameter range")
    if item.kind in {ParameterKind.INTEGER, ParameterKind.FLOAT}:
        if item.minimum is None or item.maximum is None or item.step is None:
            raise ValueError("numeric parameter range is incomplete")
        values: list[ParameterValue] = []
        current = item.minimum
        while current <= item.maximum:
            values.append(
                int(current) if item.kind is ParameterKind.INTEGER else current
            )
            current += item.step
        return tuple(values)
    if item.kind is ParameterKind.CATEGORICAL:
        return item.choices
    if item.kind is ParameterKind.BOOLEAN:
        return (False, True)
    if item.fixed_value is None:
        raise ValueError("fixed parameter range is incomplete")
    return (item.fixed_value,)


def iter_grid_candidates(
    space: ParameterSpace,
    *,
    max_candidates: int,
    max_expansion: int,
    max_constraints: int,
) -> Iterator[dict[str, ParameterValue]]:
    """Yield unique valid grid candidates after a complete cap precheck.

    Args:
        space: Bounded parameter space.
        max_candidates: Maximum valid candidate count.
        max_expansion: Maximum raw Cartesian expansion.
        max_constraints: Maximum constraint count.

    Yields:
        Active executable candidate mappings.

    Raises:
        ValueError: If bounds are exceeded or the space is invalid.
    """
    logger.info("Generating bounded Optimization grid candidates")
    if max_candidates <= 0:
        logger.bind(
            event="optimization.validation_failure",
            result="validation_failed",
            limit_name="max_candidates",
            max_candidates=max_candidates,
        ).warning("Rejected invalid Optimization grid candidate cap")
        raise ValueError("max_candidates must be positive")
    validate_parameter_space(
        space,
        max_expansion=max_expansion,
        max_constraints=max_constraints,
    )
    names = tuple(item.name for item in space.parameters)
    candidate_count = 0
    for _ in _iter_valid_candidates(space, names):
        candidate_count += 1
        if candidate_count > max_candidates:
            logger.bind(
                event="optimization.cap_rejection",
                result="cap_rejected",
                limit_name="max_candidates",
                max_candidates=max_candidates,
                candidate_count=candidate_count,
            ).warning("Rejected Optimization grid exceeding candidate cap")
            raise ValueError("valid grid candidate count exceeds the configured cap")
    if candidate_count == 0:
        logger.bind(
            event="optimization.validation_failure",
            result="validation_failed",
            candidate_count=0,
        ).warning("Rejected Optimization grid without valid candidates")
        raise ValueError("parameter space yields no valid candidates")
    yield from _iter_valid_candidates(space, names)


def _iter_valid_candidates(
    space: ParameterSpace,
    names: tuple[str, ...],
) -> Iterator[dict[str, ParameterValue]]:
    """Yield deduplicated executable candidates without Cartesian materialization.

    Args:
        space: Validated bounded parameter space.
        names: Parameter names in product order.

    Yields:
        Unique executable candidate mappings.
    """
    logger.debug("Iterating valid Optimization grid candidates")
    identities: set[str] = set()
    for combination in itertools.product(*(_values(item) for item in space.parameters)):
        raw = dict(zip(names, combination, strict=True))
        if not evaluate_constraints(raw, space.constraints):
            continue
        executable = get_executable_parameters(raw, space)
        identity = canonical_json(executable)
        if identity not in identities:
            identities.add(identity)
            yield executable


__all__ = ["iter_grid_candidates"]
