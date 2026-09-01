"""OperatingEnvelope v1 private model and transport."""

# mypy: disable-error-code="arg-type"
# ruff: noqa: DOC201

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, model_validator

from app.composition.logging import get_logger
from app.kernel.serialization import to_json_safe

logger = get_logger(__name__)


class _OperatingEnvelope(BaseModel):
    """Private immutable operating limits for one Strategy profile."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.operating_envelope.v1"] = (
        "strategy.operating_envelope.v1"
    )
    envelope_id: str
    max_volatility: Decimal
    max_spread: Decimal
    min_liquidity: Decimal
    permitted_regimes: tuple[str, ...]
    permitted_sessions: tuple[str, ...]
    max_holding_seconds: int
    blocked_event_types: tuple[str, ...]

    @model_validator(mode="after")
    def _validate(self) -> _OperatingEnvelope:
        if (
            not self.envelope_id.strip()
            or not self.permitted_regimes
            or not self.permitted_sessions
        ):
            raise ValueError(
                "operating envelope identity, regimes, and sessions are required"
            )
        if self.max_holding_seconds <= 0:
            raise ValueError("max_holding_seconds must be positive")
        for value in (self.max_volatility, self.max_spread, self.min_liquidity):
            if not value.is_finite() or value < 0:
                raise ValueError(
                    "operating envelope thresholds must be finite and non-negative"
                )
        return self


def build_operating_envelope(
    *,
    envelope_id: str,
    max_volatility: Decimal,
    max_spread: Decimal,
    min_liquidity: Decimal,
    permitted_regimes: Sequence[str],
    permitted_sessions: Sequence[str],
    max_holding_seconds: int,
    blocked_event_types: Sequence[str],
) -> dict[str, Any]:
    """Build a validated JSON-safe OperatingEnvelope v1 mapping."""
    logger.info("Building operating envelope")
    model = _OperatingEnvelope(
        envelope_id=envelope_id,
        max_volatility=max_volatility,
        max_spread=max_spread,
        min_liquidity=min_liquidity,
        permitted_regimes=tuple(permitted_regimes),
        permitted_sessions=tuple(permitted_sessions),
        max_holding_seconds=max_holding_seconds,
        blocked_event_types=tuple(blocked_event_types),
    )
    return dict(to_json_safe(model.model_dump(mode="json")))


def parse_operating_envelope(value: Mapping[str, object]) -> dict[str, Any]:
    """Parse a strict OperatingEnvelope v1 mapping."""
    return dict(
        to_json_safe(
            _OperatingEnvelope.model_validate(dict(value)).model_dump(mode="json")
        )
    )


__all__ = ["build_operating_envelope", "parse_operating_envelope"]
