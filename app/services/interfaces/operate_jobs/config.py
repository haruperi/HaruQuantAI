"""Strict empty configuration for the jobs interface."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OperateJobsConfig:
    """Task 1.26 owns no feature-local configuration keys."""


def from_dict(raw: dict[str, object] | None) -> OperateJobsConfig:
    """Validate an empty configuration mapping."""
    raw = {} if raw is None else raw
    if raw:
        raise ValueError(f"unknown operate-jobs config keys: {sorted(raw)}")
    return OperateJobsConfig()
