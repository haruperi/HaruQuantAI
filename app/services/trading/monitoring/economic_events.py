# ruff: noqa: DOC201, DOC501
"""Versioned economic execution-event transport for later Portfolio ingestion."""

from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.utils import to_json_safe


class _EconomicExecutionEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["trading.economic_execution_event.v1"] = (
        "trading.economic_execution_event.v1"
    )
    event_id: str
    event_type: Literal[
        "fill",
        "fee_estimate",
        "correction",
        "financing_trigger",
        "corporate_action_trigger",
        "liquidation",
    ]
    order_id: str
    position_id: str | None = None
    correlation_id: str
    causation_id: str | None = None
    payload: Mapping[str, Any]


def build_economic_execution_event(**values: object) -> dict[str, Any]:
    """Build one validated JSON-safe economic execution event."""
    model = _EconomicExecutionEvent.model_validate(values)
    safe = to_json_safe(model.model_dump(mode="json"))
    if not isinstance(safe, dict):
        raise TypeError("economic event transport must be a mapping")
    return safe


def parse_economic_execution_event(value: Mapping[str, object]) -> object:
    """Parse one economic execution event mapping."""
    return _EconomicExecutionEvent.model_validate(value)


__all__ = ["build_economic_execution_event", "parse_economic_execution_event"]
