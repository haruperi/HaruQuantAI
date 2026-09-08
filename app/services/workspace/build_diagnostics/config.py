"""Strict diagnostic bounds."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BuildDiagnosticsConfig:
    max_records: int = 500
    max_bytes: int = 1_000_000


def from_dict(raw: dict[str, object] | None) -> BuildDiagnosticsConfig:
    raw = {} if raw is None else raw
    unknown = set(raw) - {"max_records", "max_bytes"}
    if unknown:
        raise ValueError(f"unknown build-diagnostics config keys: {sorted(unknown)}")
    records = int(raw.get("max_records", 500)); size = int(raw.get("max_bytes", 1_000_000))
    if not 1 <= records <= 10_000 or not 1024 <= size <= 50_000_000:
        raise ValueError("diagnostic bounds are invalid")
    return BuildDiagnosticsConfig(records, size)
