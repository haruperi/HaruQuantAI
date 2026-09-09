#!/usr/bin/env python3
"""Deterministic failure classification and bounded correction routing."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Final, TypeVar

MAX_DIRECT_CORRECTIONS: Final[int] = 2
MAX_OPERATION_RETRIES: Final[int] = 1
T = TypeVar("T")


class FailureClass(StrEnum):
    """Supported failure classes for one Task workflow run."""

    IMPLEMENTATION_FIX = "IMPLEMENTATION_FIX"
    DESIGN_CHANGE = "DESIGN_CHANGE"
    ADMINISTRATIVE_RETRY = "ADMINISTRATIVE_RETRY"
    ENVIRONMENT_FAILURE = "ENVIRONMENT_FAILURE"


@dataclass(frozen=True, slots=True)
class FailureRoute:
    """One deterministic route selected from a classified failure."""

    target: str
    requires_reasoning: bool
    exhausted: bool = False


def route_failure(
    failure_class: FailureClass,
    *,
    direct_corrections: int = 0,
    operation_retries: int = 0,
) -> FailureRoute:
    """Return the bounded route for a classified failure.

    Args:
        failure_class: Classification emitted by review or the controller.
        direct_corrections: Direct correction rounds already used.
        operation_retries: Retries already used for the exact operation.

    Returns:
        Fail-closed routing decision.
    """
    if failure_class is FailureClass.IMPLEMENTATION_FIX:
        if direct_corrections >= MAX_DIRECT_CORRECTIONS:
            return FailureRoute("PLANNER", requires_reasoning=True, exhausted=True)
        return FailureRoute("EXECUTOR", requires_reasoning=True)
    if failure_class is FailureClass.DESIGN_CHANGE:
        return FailureRoute("PLANNER", requires_reasoning=True)
    if operation_retries >= MAX_OPERATION_RETRIES:
        return FailureRoute("STOP", requires_reasoning=False, exhausted=True)
    return FailureRoute("CONTROLLER_RETRY", requires_reasoning=False)


def validate_administrative_paths(paths: list[str] | tuple[str, ...]) -> None:
    """Reject an administrative repair that targets authoritative source.

    Administrative recovery is limited to ignored run/log storage and the
    replace-only next-role artifact. Journals and repository source remain
    outside this authority.

    Args:
        paths: Repository-relative POSIX paths proposed for repair.

    Raises:
        ValueError: If any path is absolute, traverses upward, or is not in the
            narrow administrative allowlist.
    """
    for raw_path in paths:
        normalized = raw_path.replace("\\", "/")
        path = PurePosixPath(normalized)
        allowed = normalized.startswith((".agents/runs/", ".agents/logs/")) or (
            normalized == ".agents/task/next-agent.md"
        )
        if path.is_absolute() or ".." in path.parts or not allowed:
            raise ValueError(f"Administrative recovery cannot modify {raw_path!r}.")


def run_bounded_environment_operation(operation: Callable[[], T]) -> T:
    """Retry one exact operation once only for process-environment failure.

    Args:
        operation: Idempotent or read-only operation over unchanged inputs.

    Returns:
        Operation result.

    Raises:
        OSError: If the identical second attempt also fails.
    """
    try:
        return operation()
    except OSError:
        return operation()
