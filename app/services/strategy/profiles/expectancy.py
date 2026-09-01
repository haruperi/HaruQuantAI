"""Fail-closed approved-expectancy reference consumer port."""

# mypy: disable-error-code="arg-type"
# ruff: noqa: DOC201, DOC501

from collections.abc import Callable, Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.composition.logging import get_logger
from app.kernel.serialization import to_json_safe

logger = get_logger(__name__)


class _ExpectancyReference(BaseModel):
    """Private version-exact Research profile reference."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.expectancy_reference.v1"] = (
        "strategy.expectancy_reference.v1"
    )
    profile_id: str
    exact_version: str
    evidence_ref: str


def build_expectancy_reference(
    *, profile_id: str, exact_version: str, evidence_ref: str
) -> dict[str, Any]:
    """Build a version-exact expectancy reference without Research evidence."""
    logger.info("Building strategy profile version-exact expectancy reference")
    model = _ExpectancyReference(
        profile_id=profile_id, exact_version=exact_version, evidence_ref=evidence_ref
    )
    if any(not str(item).strip() for item in (profile_id, exact_version, evidence_ref)):
        raise ValueError("expectancy reference fields must be non-empty")
    return dict(to_json_safe(model.model_dump(mode="json")))


def parse_expectancy_reference(value: Mapping[str, object]) -> dict[str, Any]:
    """Parse a strict expectancy reference."""
    return build_expectancy_reference(
        **_ExpectancyReference.model_validate(dict(value)).model_dump(
            exclude={"contract_version", "schema_id"}
        )
    )


def evaluate_expectancy_reference(
    reference: Mapping[str, object],
    *,
    provider: Callable[[Mapping[str, object]], Mapping[str, object]] | None = None,
) -> str:
    """Return eligibility only from an exact authoritative provider response."""
    parsed = parse_expectancy_reference(reference)
    if provider is None:
        logger.warning(
            "Expectancy provider unavailable; applying normal risk-to-reward fallback"
        )
        return "NOT_ELIGIBLE"
    try:
        result = provider(parsed)
    except RuntimeError, TypeError, ValueError:
        logger.warning("Expectancy provider failed; applying fail-closed fallback")
        return "NOT_ELIGIBLE"
    return (
        "ELIGIBLE"
        if result.get("status") == "ELIGIBLE"
        and result.get("profile_id") == parsed["profile_id"]
        and result.get("exact_version") == parsed["exact_version"]
        else "NOT_ELIGIBLE"
    )


__all__ = [
    "build_expectancy_reference",
    "evaluate_expectancy_reference",
    "parse_expectancy_reference",
]
