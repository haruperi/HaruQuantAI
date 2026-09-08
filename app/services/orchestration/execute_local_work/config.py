"""Strict bounds for local worker execution."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecuteLocalWorkConfig:
    max_input_bytes: int = 64 * 1024 * 1024
    cancellation_grace_seconds: float = 1.5


def from_dict(raw: dict[str, object] | None) -> ExecuteLocalWorkConfig:
    raw = {} if raw is None else raw
    unknown = set(raw) - {"max_input_bytes", "cancellation_grace_seconds"}
    if unknown:
        raise ValueError(f"unknown execute-local-work config keys: {sorted(unknown)}")
    size = int(raw.get("max_input_bytes", 64 * 1024 * 1024))
    grace = float(raw.get("cancellation_grace_seconds", 1.5))
    if size < 1 or size > 2 * 1024 * 1024 * 1024 or not 0.1 <= grace <= 2.0:
        raise ValueError("local worker bounds are invalid")
    return ExecuteLocalWorkConfig(size, grace)
