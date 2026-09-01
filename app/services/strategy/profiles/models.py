"""Versioned Strategy operational profile transport."""

# mypy: disable-error-code="arg-type"
# ruff: noqa: DOC201

from collections.abc import Mapping, Sequence
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator

from app.composition.logging import get_logger
from app.kernel.serialization import to_json_safe

logger = get_logger(__name__)


class _StrategyProfile(BaseModel):
    """Private immutable StrategyProfile v1 contract."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.profile.v1"] = "strategy.profile.v1"
    strategy_id: str
    strategy_version: str
    permitted_instruments: tuple[str, ...]
    permitted_sessions: tuple[str, ...]
    permitted_regimes: tuple[str, ...]
    indicator_dependencies: tuple[str, ...]
    entry_rules: tuple[str, ...]
    exit_rules: tuple[str, ...]
    invalidation_rules: tuple[str, ...]
    automation_permissions: tuple[
        Literal["OFF", "ADVISORY", "SUPERVISED", "AUTOMATED"], ...
    ]

    @field_validator("strategy_id", "strategy_version")
    @classmethod
    def _text(cls, value: str) -> str:
        if not value or value != value.strip():
            raise ValueError("profile identity must be non-empty and trimmed")
        return value

    @field_validator(
        "permitted_instruments",
        "permitted_sessions",
        "permitted_regimes",
        "indicator_dependencies",
        "entry_rules",
        "exit_rules",
        "invalidation_rules",
        "automation_permissions",
    )
    @classmethod
    def _unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if (
            not value
            or len(value) != len(set(value))
            or any(not item.strip() for item in value)
        ):
            raise ValueError(
                "profile collections must be non-empty, unique, and trimmed"
            )
        return value


def build_strategy_profile(
    *,
    strategy_id: str,
    strategy_version: str,
    permitted_instruments: Sequence[str],
    permitted_sessions: Sequence[str],
    permitted_regimes: Sequence[str],
    indicator_dependencies: Sequence[str],
    entry_rules: Sequence[str],
    exit_rules: Sequence[str],
    invalidation_rules: Sequence[str],
    automation_permissions: Sequence[str],
) -> dict[str, Any]:
    """Build a validated JSON-safe StrategyProfile v1 mapping."""
    logger.info("Building StrategyProfile contract")
    model = _StrategyProfile(
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        permitted_instruments=tuple(permitted_instruments),
        permitted_sessions=tuple(permitted_sessions),
        permitted_regimes=tuple(permitted_regimes),
        indicator_dependencies=tuple(indicator_dependencies),
        entry_rules=tuple(entry_rules),
        exit_rules=tuple(exit_rules),
        invalidation_rules=tuple(invalidation_rules),
        automation_permissions=tuple(automation_permissions),
    )
    return dict(to_json_safe(model.model_dump(mode="json")))


def parse_strategy_profile(value: Mapping[str, object]) -> dict[str, Any]:
    """Parse a strict StrategyProfile v1 mapping, rejecting incompatible input."""
    logger.info("Parsing StrategyProfile contract")
    model = _StrategyProfile.model_validate(dict(value))
    return dict(to_json_safe(model.model_dump(mode="json")))


__all__ = ["build_strategy_profile", "parse_strategy_profile"]
