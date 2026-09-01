"""Canonical immutable NoTradeOutcome v1 transport."""

# mypy: disable-error-code="arg-type"
# ruff: noqa: DOC201

from collections.abc import Mapping
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.composition.logging import get_logger
from app.kernel.serialization import canonical_digest, to_json_safe

logger = get_logger(__name__)


class _NoTradeOutcome(BaseModel):
    """Private no-trade classification artifact."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["risk.no_trade_outcome.v1"] = "risk.no_trade_outcome.v1"
    outcome_id: str
    decision_id: str
    outcome_kind: Literal["safe_stand_down", "failed_gameplay"]
    failed_rule_ids: tuple[str, ...]
    rationale: str
    evaluated_at: datetime

    @field_validator("evaluated_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("NoTradeOutcome timestamp must be timezone-aware")
        return value

    @model_validator(mode="after")
    def _relationships(self) -> _NoTradeOutcome:
        if not self.outcome_id.strip() or not self.decision_id.strip():
            raise ValueError("NoTradeOutcome identity text must be non-empty")
        if not self.failed_rule_ids:
            raise ValueError("NoTradeOutcome requires at least one failed rule")
        if not self.rationale.strip():
            raise ValueError("NoTradeOutcome requires a non-empty rationale")
        return self


def build_no_trade_outcome(
    *,
    decision_id: str,
    outcome_kind: str,
    failed_rule_ids: tuple[str, ...],
    rationale: str,
    evaluated_at: datetime,
) -> dict[str, Any]:
    """Build a deterministic JSON-safe NoTradeOutcome v1 mapping."""
    fields = {
        "decision_id": decision_id,
        "outcome_kind": outcome_kind,
        "failed_rule_ids": failed_rule_ids,
        "rationale": rationale,
        "evaluated_at": evaluated_at,
    }
    material = fields | {
        "contract_version": "v1",
        "schema_id": "risk.no_trade_outcome.v1",
    }
    outcome_id = f"notrade-{canonical_digest(material)}"
    logger.info("Building NoTradeOutcome %s", outcome_id)
    model = _NoTradeOutcome(outcome_id=outcome_id, **fields)
    return dict(to_json_safe(model.model_dump(mode="json")))


def parse_no_trade_outcome(value: Mapping[str, object]) -> dict[str, Any]:
    """Parse a strict NoTradeOutcome v1 mapping."""
    logger.info("Parsing NoTradeOutcome contract")
    return dict(
        to_json_safe(
            _NoTradeOutcome.model_validate(dict(value)).model_dump(mode="json")
        )
    )


__all__ = ["build_no_trade_outcome", "parse_no_trade_outcome"]
