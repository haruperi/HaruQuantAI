"""Strict result bounds for tool governance."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GovernToolCallsConfig:
    max_result_bytes: int = 262144


def from_dict(raw: dict[str, object] | None) -> GovernToolCallsConfig:
    raw = {} if raw is None else raw
    if set(raw) - {"max_result_bytes"}: raise ValueError("unknown govern-tool-calls config key")
    value = int(raw.get("max_result_bytes", 262144))
    if not 1024 <= value <= 16_777_216: raise ValueError("max_result_bytes is invalid")
    return GovernToolCallsConfig(value)
