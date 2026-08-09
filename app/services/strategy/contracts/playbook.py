"""Strategy playbook and setup-evaluation transports."""

# mypy: disable-error-code="arg-type"
# ruff: noqa: DOC201

from collections.abc import Mapping, Sequence
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.utils import get_logger, to_json_safe

logger = get_logger(__name__)


class _StrategyPlaybook(BaseModel):
    """Private immutable playbook contract."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.playbook.v1"] = "strategy.playbook.v1"
    playbook_id: str
    strategy_profile_ref: str
    title: str
    summary: str
    setup_rules: tuple[str, ...]
    debrief_prompts: tuple[str, ...]

    @field_validator("playbook_id", "strategy_profile_ref", "title", "summary")
    @classmethod
    def _text(cls, value: str) -> str:
        if not value or value != value.strip():
            raise ValueError("playbook text must be non-empty and trimmed")
        return value

    @field_validator("setup_rules", "debrief_prompts")
    @classmethod
    def _items(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if (
            not value
            or len(value) != len(set(value))
            or any(not item.strip() for item in value)
        ):
            raise ValueError("playbook items must be non-empty and unique")
        return value


class _SetupEvaluation(BaseModel):
    """Private point-in-time setup evaluation contract."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.setup_evaluation.v1"] = "strategy.setup_evaluation.v1"
    evaluation_id: str
    playbook_ref: str
    outcome: Literal[
        "MATCH", "NO_MATCH", "STALE", "REGIME_MISMATCH", "INSUFFICIENT_EVIDENCE"
    ]
    source_snapshot_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]

    @model_validator(mode="after")
    def _shape(self) -> _SetupEvaluation:
        if not self.evaluation_id.strip() or not self.playbook_ref.strip():
            raise ValueError("evaluation identity must be non-empty")
        if not self.source_snapshot_refs:
            raise ValueError("setup evaluation requires source snapshots")
        if self.outcome == "MATCH" and self.reason_codes:
            raise ValueError("MATCH cannot carry failure reasons")
        if self.outcome != "MATCH" and not self.reason_codes:
            raise ValueError("non-match outcomes require reason codes")
        return self


def build_strategy_playbook(
    *,
    playbook_id: str,
    strategy_profile_ref: str,
    title: str,
    summary: str,
    setup_rules: Sequence[str],
    debrief_prompts: Sequence[str],
) -> dict[str, Any]:
    """Build a validated JSON-safe playbook mapping."""
    logger.info("Building Strategy playbook")
    model = _StrategyPlaybook(
        playbook_id=playbook_id,
        strategy_profile_ref=strategy_profile_ref,
        title=title,
        summary=summary,
        setup_rules=tuple(setup_rules),
        debrief_prompts=tuple(debrief_prompts),
    )
    return dict(to_json_safe(model.model_dump(mode="json")))


def parse_strategy_playbook(value: Mapping[str, object]) -> dict[str, Any]:
    """Parse a strict Strategy playbook mapping."""
    return dict(
        to_json_safe(
            _StrategyPlaybook.model_validate(dict(value)).model_dump(mode="json")
        )
    )


def build_setup_evaluation(
    *,
    evaluation_id: str,
    playbook_ref: str,
    outcome: str,
    source_snapshot_refs: Sequence[str],
    reason_codes: Sequence[str] = (),
) -> dict[str, Any]:
    """Build a deterministic SetupEvaluation v1 mapping."""
    logger.info("Building setup evaluation with outcome %s", outcome)
    model = _SetupEvaluation(
        evaluation_id=evaluation_id,
        playbook_ref=playbook_ref,
        outcome=outcome,
        source_snapshot_refs=tuple(source_snapshot_refs),
        reason_codes=tuple(reason_codes),
    )
    return dict(to_json_safe(model.model_dump(mode="json")))


def parse_setup_evaluation(value: Mapping[str, object]) -> dict[str, Any]:
    """Parse a strict SetupEvaluation v1 mapping."""
    return dict(
        to_json_safe(
            _SetupEvaluation.model_validate(dict(value)).model_dump(mode="json")
        )
    )


__all__ = [
    "build_setup_evaluation",
    "build_strategy_playbook",
    "parse_setup_evaluation",
    "parse_strategy_playbook",
]
