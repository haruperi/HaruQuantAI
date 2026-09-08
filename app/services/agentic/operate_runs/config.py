"""Strict configuration for Agentic operations."""

from dataclasses import dataclass


@dataclass(frozen=True)
class OperateRunsConfig:
    max_payload_chars: int = 4096


def from_dict(raw: dict[str, object] | None) -> OperateRunsConfig:
    raw = {} if raw is None else raw
    unknown = set(raw) - {"max_payload_chars"}
    if unknown:
        raise ValueError(f"unknown operate-runs config keys: {sorted(unknown)}")
    value = int(raw.get("max_payload_chars", 4096))
    if value < 128 or value > 65536:
        raise ValueError("max_payload_chars must be 128..65536")
    return OperateRunsConfig(value)
