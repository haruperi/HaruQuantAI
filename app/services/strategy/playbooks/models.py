"""Strategy playbook transport."""

# mypy: disable-error-code="arg-type"
# ruff: noqa: DOC201

from collections.abc import Mapping, Sequence
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator

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


__all__ = ["build_strategy_playbook", "parse_strategy_playbook"]
