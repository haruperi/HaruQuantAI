"""ExitPlan v1 private model and transport."""

# mypy: disable-error-code="arg-type"
# ruff: noqa: DOC201

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, model_validator

from app.utils import get_logger, to_json_safe

logger = get_logger(__name__)


class _ExitPlan(BaseModel):
    """Private immutable exit and management plan."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.exit_plan.v1"] = "strategy.exit_plan.v1"
    exit_plan_id: str
    initial_stop: Decimal
    target: Decimal
    partial_exit_fractions: tuple[Decimal, ...]
    trailing_rule: str | None
    time_stop_seconds: int | None
    invalidation_rule: str
    automation_handoff: Literal["NONE", "ADVISORY", "SUPERVISED", "AUTOMATED"]

    @model_validator(mode="after")
    def _validate(self) -> _ExitPlan:
        if not self.exit_plan_id.strip() or not self.invalidation_rule.strip():
            raise ValueError("exit plan identity and invalidation rule are required")
        if any(
            not value.is_finite() or value <= 0
            for value in (self.initial_stop, self.target)
        ):
            raise ValueError("exit plan prices must be finite and positive")
        if any(
            not value.is_finite() or value <= 0 or value >= 1
            for value in self.partial_exit_fractions
        ):
            raise ValueError("partial exit fractions must be between zero and one")
        if sum(self.partial_exit_fractions, Decimal(0)) > 1:
            raise ValueError("partial exits cannot exceed the full position")
        if self.time_stop_seconds is not None and self.time_stop_seconds <= 0:
            raise ValueError("time stop must be positive")
        return self


def build_exit_plan(
    *,
    exit_plan_id: str,
    initial_stop: Decimal,
    target: Decimal,
    partial_exit_fractions: Sequence[Decimal],
    trailing_rule: str | None,
    time_stop_seconds: int | None,
    invalidation_rule: str,
    automation_handoff: str,
) -> dict[str, Any]:
    """Build a validated JSON-safe ExitPlan v1 mapping."""
    logger.info("Building exit plan")
    model = _ExitPlan(
        exit_plan_id=exit_plan_id,
        initial_stop=initial_stop,
        target=target,
        partial_exit_fractions=tuple(partial_exit_fractions),
        trailing_rule=trailing_rule,
        time_stop_seconds=time_stop_seconds,
        invalidation_rule=invalidation_rule,
        automation_handoff=automation_handoff,
    )
    return dict(to_json_safe(model.model_dump(mode="json")))


def parse_exit_plan(value: Mapping[str, object]) -> dict[str, Any]:
    """Parse a strict ExitPlan v1 mapping."""
    return dict(
        to_json_safe(_ExitPlan.model_validate(dict(value)).model_dump(mode="json"))
    )


__all__ = ["build_exit_plan", "parse_exit_plan"]
