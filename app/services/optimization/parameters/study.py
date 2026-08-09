"""OptimizationStudy v1 — dataset/replay identity and budget contract.

This module implements the application Phase 0 ``feature`` addition to
``FEAT-OPT-01``/``FEAT-OPT-06``: an Optimization-owned versioned study identity that
binds a bounded search to the dataset it runs over, a deterministic replay identity,
and the approved resource budget. Per decision D-1 the contract travels as a validated
JSON-safe mapping behind ``build_optimization_study``/``parse_optimization_study``; the
Pydantic model stays private.

The study is advisory provenance metadata. It never confers execution, promotion, or
live-trading authority, and it never substitutes for the durable ``OptimizationResult``
evidence assembled by the evidence feature.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.utils import canonical_json, get_logger, to_json_safe

logger = get_logger(__name__)

STUDY_CONTRACT_VERSION: Literal["v1"] = "v1"
STUDY_SCHEMA_ID: Literal["optimization.study.v1"] = "optimization.study.v1"

_SHA256_HEX_LENGTH = 64


class _OptimizationStudy(BaseModel):
    """Private immutable Optimization study identity and budget."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: Literal["v1"] = STUDY_CONTRACT_VERSION
    schema_id: Literal["optimization.study.v1"] = STUDY_SCHEMA_ID
    study_id: str
    strategy_ref: str
    market_data_ref: str
    dataset_id: str
    dataset_hash: str
    replay_identity: str
    objective_hash: str
    space_hash: str
    max_candidates: int
    max_runtime_seconds: Decimal
    max_monte_carlo_simulations: int
    request_id: str
    correlation_id: str
    created_at: str
    non_binding: Literal[True] = True

    @field_validator(
        "study_id",
        "strategy_ref",
        "market_data_ref",
        "dataset_id",
        "replay_identity",
        "request_id",
        "correlation_id",
        "created_at",
    )
    @classmethod
    def _validate_required_text(cls, value: str) -> str:
        """Validate that a required textual field is non-empty.

        Args:
            value: Text to validate.

        Returns:
            The validated non-blank text.

        Raises:
            ValueError: If the text is blank.
        """
        if not value or value != value.strip():
            raise ValueError("study text fields must be non-empty")
        return value

    @field_validator("dataset_hash", "objective_hash", "space_hash")
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        """Validate that a provenance hash is a lowercase SHA-256 digest.

        Args:
            value: Hash to validate.

        Returns:
            The validated digest.

        Raises:
            ValueError: If the digest is malformed.
        """
        if len(value) != _SHA256_HEX_LENGTH or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise ValueError("study provenance hashes must be lowercase SHA-256")
        return value

    @model_validator(mode="after")
    def _validate_budget(self) -> _OptimizationStudy:
        """Validate approved resource budget bounds and identity uniqueness.

        Returns:
            The validated study.

        Raises:
            ValueError: If budget caps are non-positive/non-finite or provenance
                identities collide in a way that would erase traceability.
        """
        if self.max_candidates <= 0:
            raise ValueError("max_candidates must be positive")
        if self.max_monte_carlo_simulations <= 0:
            raise ValueError("max_monte_carlo_simulations must be positive")
        if not self.max_runtime_seconds.is_finite() or self.max_runtime_seconds <= 0:
            raise ValueError("max_runtime_seconds must be finite and positive")
        # Dataset and replay identities must be distinct fields so a replay over a
        # different dataset cannot masquerade as the original study (anti-leakage).
        if self.dataset_id == self.replay_identity:
            raise ValueError("dataset_id and replay_identity must be distinct")
        return self


def build_optimization_study(
    *,
    study_id: str,
    strategy_ref: str,
    market_data_ref: str,
    dataset_id: str,
    dataset_hash: str,
    replay_identity: str,
    objective_hash: str,
    space_hash: str,
    max_candidates: int,
    max_runtime_seconds: Decimal,
    max_monte_carlo_simulations: int,
    request_id: str,
    correlation_id: str,
    created_at: str,
) -> dict[str, Any]:
    """Build a validated JSON-safe OptimizationStudy v1 mapping.

    Args:
        study_id: Canonical study identifier (e.g. ``study-<uuid>``).
        strategy_ref: Approved Strategy version reference the study is bound to.
        market_data_ref: Approved Data source reference for the search window.
        dataset_id: Immutable dataset identity the search runs over.
        dataset_hash: SHA-256 provenance digest of the dataset payload.
        replay_identity: Deterministic replay identity (distinct from dataset_id).
        objective_hash: SHA-256 digest of the enabled objective provenance.
        space_hash: SHA-256 parameter-space provenance digest.
        max_candidates: Approved bounded-search candidate cap.
        max_runtime_seconds: Approved bounded-search wall-clock cap.
        max_monte_carlo_simulations: Approved Monte Carlo path cap.
        request_id: Request identifier for trace propagation.
        correlation_id: Correlation identifier for trace propagation.
        created_at: Aware-UTC ISO-8601 timestamp the study was authored.

    Returns:
        Deterministic JSON-safe ``optimization.study.v1`` mapping.

    Raises:
        ValueError: If any provenance, identity, or budget field is invalid.
        TypeError: If the serialized payload is not a JSON-safe mapping.
    """
    logger.info("Building OptimizationStudy v1 mapping")
    model = _OptimizationStudy(
        study_id=study_id,
        strategy_ref=strategy_ref,
        market_data_ref=market_data_ref,
        dataset_id=dataset_id,
        dataset_hash=dataset_hash,
        replay_identity=replay_identity,
        objective_hash=objective_hash,
        space_hash=space_hash,
        max_candidates=max_candidates,
        max_runtime_seconds=max_runtime_seconds,
        max_monte_carlo_simulations=max_monte_carlo_simulations,
        request_id=request_id,
        correlation_id=correlation_id,
        created_at=created_at,
    )
    safe = to_json_safe(model.model_dump(mode="json"))
    if not isinstance(safe, dict):
        raise TypeError("OptimizationStudy serialization is unsafe")
    return dict(safe)


def parse_optimization_study(mapping: Mapping[str, object]) -> dict[str, Any]:
    """Validate a strict OptimizationStudy v1 mapping and return it JSON-safe.

    Args:
        mapping: Contract mapping to validate.

    Returns:
        Deterministic JSON-safe ``optimization.study.v1`` mapping.

    Raises:
        ValueError: If the mapping is incompatible, non-canonical, or missing
            required provenance.
        TypeError: If the serialized payload is not a JSON-safe mapping.
    """
    logger.info("Validating OptimizationStudy v1 mapping")
    data = dict(mapping)
    if data.get("contract_version") != STUDY_CONTRACT_VERSION:
        raise ValueError("OptimizationStudy contract version is unsupported")
    if data.get("schema_id") != STUDY_SCHEMA_ID:
        raise ValueError("OptimizationStudy schema id is unsupported")
    model = _OptimizationStudy.model_validate(data)
    safe = to_json_safe(model.model_dump(mode="json"))
    if not isinstance(safe, dict):
        raise TypeError("OptimizationStudy serialization is unsafe")
    # Canonical serialization must round-trip; a divergence signals non-JSON-safe
    # input that would silently drop provenance downstream.
    canonical_json(safe)
    return dict(safe)


def get_optimization_study_contract_version() -> str:
    """Return the OptimizationStudy contract version.

    Returns:
        The canonical ``v1`` contract version string.
    """
    return STUDY_CONTRACT_VERSION


def get_optimization_study_schema_id() -> str:
    """Return the OptimizationStudy schema identifier.

    Returns:
        The canonical ``optimization.study.v1`` schema identifier string.
    """
    return STUDY_SCHEMA_ID


__all__ = [
    "STUDY_CONTRACT_VERSION",
    "STUDY_SCHEMA_ID",
    "build_optimization_study",
    "get_optimization_study_contract_version",
    "get_optimization_study_schema_id",
    "parse_optimization_study",
]
