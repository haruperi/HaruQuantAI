"""Fail-closed Portfolio construction evidence validation."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from types import MappingProxyType
from typing import TYPE_CHECKING

from pydantic import BaseModel

from app.services.analytics import PortfolioAllocationEvidence
from app.services.data.contracts import (
    AccountStateSnapshot,
    FXConversionEvidence,
    MarketDataset,
)
from app.services.portfolio.exceptions import PortfolioError
from app.services.risk import DecisionState, StrategyOperationalEligibilityDecision
from app.services.strategy import StrategyLifecycleStatus, ValidatedStrategyRef
from app.utils import canonical_json, logger

if TYPE_CHECKING:
    from app.services.portfolio.config import PortfolioSettings
    from app.services.portfolio.contracts import PortfolioConstructionRequest


def _digest(value: object) -> str:
    """Hash one supported immutable owner value.

    Args:
        value: Supported canonical value.

    Returns:
        Lowercase SHA-256 digest.
    """
    logger.debug("Hashing immutable Portfolio owner evidence")
    return hashlib.sha256(
        canonical_json(_hash_material(value)).encode("utf-8")
    ).hexdigest()


def _hash_material(value: object) -> object:
    """Convert nested Pydantic owner contracts into canonical primitives.

    Args:
        value: Supported immutable evidence value.

    Returns:
        Canonical-serialization-compatible value.
    """
    logger.debug("Preparing Portfolio owner evidence hash material")
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, Mapping):
        return {key: _hash_material(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(_hash_material(item) for item in value)
    return value


def _require_fresh(
    observed_at: datetime,
    now: datetime,
    max_age: timedelta,
    detail: str,
) -> None:
    """Require an evidence timestamp inside the configured UTC window.

    Args:
        observed_at: Evidence observation time.
        now: Current injected UTC time.
        max_age: Maximum accepted evidence age.
        detail: Boundary-safe failure detail.

    Raises:
        PortfolioError: If evidence is from the future or stale.
    """
    logger.debug("Validating Portfolio evidence freshness")
    if observed_at > now or now - observed_at > max_age:
        raise PortfolioError("PORT_EVIDENCE_INVALID", detail)


@dataclass(frozen=True, slots=True)
class ValidatedConstructionEvidence:
    """Immutable evidence set accepted for deterministic construction.

    Attributes:
        request: Validated construction request.
        strategy_refs: Ordered exact Strategy references.
        eligibility_decisions: Ordered current Risk decisions.
        account_snapshot: Exact Data account snapshot.
        market_dataset: Exact Data market dataset.
        analytics_evidence: Exact Analytics allocation evidence.
        fx_evidence: Ordered exact Data FX evidence.
        component_volatilities: Analytics-resolved component volatility values.
        component_observations: Analytics-resolved sample counts.
        evidence_hash: Digest of all evidence and metric material.
        strategy_lineage_hash: Digest of exact Strategy lineage.
    """

    request: PortfolioConstructionRequest
    strategy_refs: tuple[ValidatedStrategyRef, ...]
    eligibility_decisions: tuple[StrategyOperationalEligibilityDecision, ...]
    account_snapshot: AccountStateSnapshot
    market_dataset: MarketDataset
    analytics_evidence: PortfolioAllocationEvidence
    fx_evidence: tuple[FXConversionEvidence, ...]
    component_volatilities: Mapping[str, Decimal]
    component_observations: Mapping[str, int]
    evidence_hash: str
    strategy_lineage_hash: str

    def __post_init__(self) -> None:
        """Log creation of the validated immutable evidence bundle."""
        logger.debug("Created validated Portfolio construction evidence")


def _validate_strategy_and_eligibility(
    request: PortfolioConstructionRequest,
    strategy_refs: Mapping[str, ValidatedStrategyRef],
    eligibility_decisions: Mapping[str, StrategyOperationalEligibilityDecision],
    now: datetime,
) -> tuple[
    tuple[ValidatedStrategyRef, ...],
    tuple[StrategyOperationalEligibilityDecision, ...],
]:
    """Validate exact Strategy references and current Risk eligibility.

    Args:
        request: Validated Portfolio request.
        strategy_refs: Component-keyed Strategy references.
        eligibility_decisions: Decision-ID-keyed Risk decisions.
        now: Current injected UTC time.

    Returns:
        Ordered Strategy references and eligibility decisions.

    Raises:
        PortfolioError: If any reference or approval is missing or incompatible.
    """
    logger.info("Validating Portfolio Strategy and Risk eligibility evidence")
    if any(
        not isinstance(item, ValidatedStrategyRef) for item in strategy_refs.values()
    ):
        raise PortfolioError("PORT_UNSAFE_OBJECT", "STRATEGY_REFERENCE")
    if any(
        not isinstance(item, StrategyOperationalEligibilityDecision)
        for item in eligibility_decisions.values()
    ):
        raise PortfolioError("PORT_UNSAFE_OBJECT", "ELIGIBILITY_DECISION")
    component_ids = {component.component_id for component in request.components}
    if set(strategy_refs) != component_ids:
        raise PortfolioError("PORT_EVIDENCE_INVALID", "STRATEGY_REFERENCE_SET")
    resolved_refs: list[ValidatedStrategyRef] = []
    resolved_decisions: list[StrategyOperationalEligibilityDecision] = []
    for component in request.components:
        strategy_ref = strategy_refs[component.component_id]
        decision = eligibility_decisions.get(component.eligibility_decision_id)
        if (
            strategy_ref.manifest.strategy_id != component.strategy_id
            or strategy_ref.manifest.strategy_version != component.strategy_version
            or strategy_ref.registry_record_hash != component.registry_record_hash
            or strategy_ref.lifecycle_status is not StrategyLifecycleStatus.APPROVED
        ):
            raise PortfolioError("PORT_REFERENCE_CHANGED", "STRATEGY_REFERENCE")
        if (
            decision is None
            or decision.decision_id != component.eligibility_decision_id
            or decision.strategy_id != component.strategy_id
            or decision.strategy_version != component.strategy_version
            or dict(decision.scope) != dict(request.scope)
            or decision.state is not DecisionState.APPROVE
            or decision.suspended
            or decision.issued_at > now
            or decision.expires_at <= now
        ):
            raise PortfolioError("PORT_ELIGIBILITY_INVALID", "CURRENT_APPROVAL")
        resolved_refs.append(strategy_ref)
        resolved_decisions.append(decision)
    return tuple(resolved_refs), tuple(resolved_decisions)


def _validate_owner_evidence(
    request: PortfolioConstructionRequest,
    account_snapshot: AccountStateSnapshot,
    market_dataset: MarketDataset,
    analytics_evidence: PortfolioAllocationEvidence,
    fx_evidence: Mapping[str, FXConversionEvidence],
    now: datetime,
    settings: PortfolioSettings,
) -> tuple[FXConversionEvidence, ...]:
    """Validate exact Data and Analytics references and FX coverage.

    Args:
        request: Validated Portfolio request.
        account_snapshot: Resolved Data account snapshot.
        market_dataset: Resolved Data market dataset.
        analytics_evidence: Resolved Analytics evidence.
        fx_evidence: Evidence-ID-keyed Data FX evidence.
        now: Current injected UTC time.
        settings: Complete Portfolio settings.

    Returns:
        Ordered validated FX evidence.

    Raises:
        PortfolioError: If evidence identity, hash, freshness, or FX fails.
    """
    logger.info("Validating Portfolio Data and Analytics owner evidence")
    if (
        not isinstance(account_snapshot, AccountStateSnapshot)
        or not isinstance(market_dataset, MarketDataset)
        or not isinstance(analytics_evidence, PortfolioAllocationEvidence)
        or any(
            not isinstance(item, FXConversionEvidence) for item in fx_evidence.values()
        )
    ):
        raise PortfolioError("PORT_UNSAFE_OBJECT", "OWNER_EVIDENCE")
    references = request.evidence
    owner_rows = (
        (
            account_snapshot.request_id,
            references.account_snapshot_id,
            _digest(account_snapshot),
            references.account_snapshot_hash,
            account_snapshot.snapshot_at,
            references.account_snapshot_as_of,
        ),
        (
            market_dataset.request_id,
            references.market_dataset_id,
            _digest(market_dataset),
            references.market_dataset_hash,
            market_dataset.end,
            references.market_dataset_as_of,
        ),
        (
            analytics_evidence.evidence_id,
            references.analytics_evidence_id,
            _digest(analytics_evidence),
            references.analytics_evidence_hash,
            analytics_evidence.measurement_end,
            references.analytics_evidence_as_of,
        ),
    )
    for (
        actual_id,
        expected_id,
        actual_hash,
        expected_hash,
        actual_at,
        expected_at,
    ) in owner_rows:
        if (
            actual_id != expected_id
            or actual_hash != expected_hash
            or actual_at != expected_at
        ):
            raise PortfolioError("PORT_REFERENCE_CHANGED", "OWNER_EVIDENCE")
        _require_fresh(actual_at, now, settings.evidence_max_age(), "STALE")
    if account_snapshot.expires_at <= now:
        raise PortfolioError("PORT_EVIDENCE_INVALID", "ACCOUNT_EXPIRED")
    if analytics_evidence.base_currency != request.base_currency:
        raise PortfolioError("PORT_EVIDENCE_INVALID", "CURRENCY_MISMATCH")
    if set(fx_evidence) != set(references.fx_evidence_ids):
        raise PortfolioError("PORT_FX_EVIDENCE_INVALID", "COVERAGE")
    ordered_fx: list[FXConversionEvidence] = []
    expected_hashes = dict(
        zip(
            references.fx_evidence_ids,
            references.fx_evidence_hashes,
            strict=True,
        )
    )
    for evidence_id in references.fx_evidence_ids:
        evidence = fx_evidence[evidence_id]
        if (
            evidence.request_id != evidence_id
            or _digest(evidence) != expected_hashes[evidence_id]
            or evidence.expires_at <= now
            or evidence.as_of > now
        ):
            raise PortfolioError("PORT_FX_EVIDENCE_INVALID", "CURRENT_REFERENCE")
        ordered_fx.append(evidence)
    return tuple(ordered_fx)


def _validate_analytics_metrics(
    request: PortfolioConstructionRequest,
    component_volatilities: Mapping[str, Decimal],
    component_observations: Mapping[str, int],
) -> tuple[Mapping[str, Decimal], Mapping[str, int]]:
    """Validate caller-resolved Analytics metric material without synthesis.

    Args:
        request: Validated Portfolio request.
        component_volatilities: Resolved volatility by component.
        component_observations: Resolved sample count by component.

    Returns:
        Frozen sorted volatility and observation mappings.

    Raises:
        PortfolioError: If metric sets or values are invalid.
    """
    logger.info("Validating resolved Analytics Portfolio metrics")
    component_ids = {component.component_id for component in request.components}
    if (
        set(component_volatilities) != component_ids
        or set(component_observations) != component_ids
    ):
        raise PortfolioError("PORT_EVIDENCE_INVALID", "ANALYTICS_METRIC_SET")
    if any(
        not value.is_finite() or value <= 0 for value in component_volatilities.values()
    ) or any(
        not isinstance(value, int) or isinstance(value, bool) or value <= 0
        for value in component_observations.values()
    ):
        raise PortfolioError("PORT_EVIDENCE_INVALID", "ANALYTICS_METRICS")
    return (
        MappingProxyType(dict(sorted(component_volatilities.items()))),
        MappingProxyType(dict(sorted(component_observations.items()))),
    )


def validate_construction_evidence(
    request: PortfolioConstructionRequest,
    *,
    strategy_refs: Mapping[str, ValidatedStrategyRef],
    eligibility_decisions: Mapping[str, StrategyOperationalEligibilityDecision],
    account_snapshot: AccountStateSnapshot,
    market_dataset: MarketDataset,
    analytics_evidence: PortfolioAllocationEvidence,
    fx_evidence: Mapping[str, FXConversionEvidence],
    component_volatilities: Mapping[str, Decimal],
    component_observations: Mapping[str, int],
    now: datetime,
    settings: PortfolioSettings,
) -> ValidatedConstructionEvidence:
    """Validate a complete immutable construction evidence set.

    Args:
        request: Validated Portfolio construction request.
        strategy_refs: Component-keyed exact Strategy references.
        eligibility_decisions: Decision-ID-keyed Risk eligibility decisions.
        account_snapshot: Resolved Data account snapshot.
        market_dataset: Resolved Data market dataset.
        analytics_evidence: Resolved Analytics allocation evidence.
        fx_evidence: Evidence-ID-keyed Data FX evidence.
        component_volatilities: Analytics-resolved volatility values.
        component_observations: Analytics-resolved sample counts.
        now: Current injected aware UTC time.
        settings: Complete Portfolio settings.

    Returns:
        Validated immutable evidence set.

    Raises:
        PortfolioError: If any owner reference or evidence gate fails.
    """
    logger.info("Validating complete Portfolio construction evidence")
    if now.tzinfo is None or now.utcoffset() != timedelta(0):
        raise PortfolioError("PORT_INVALID_INPUT", "NOW_NOT_UTC")
    strategy_values, decision_values = _validate_strategy_and_eligibility(
        request,
        strategy_refs,
        eligibility_decisions,
        now,
    )
    fx_values = _validate_owner_evidence(
        request,
        account_snapshot,
        market_dataset,
        analytics_evidence,
        fx_evidence,
        now,
        settings,
    )
    volatilities, observations = _validate_analytics_metrics(
        request,
        component_volatilities,
        component_observations,
    )
    strategy_hash = _digest(strategy_values)
    evidence_hash = _digest(
        {
            "account_snapshot": account_snapshot,
            "analytics_evidence": analytics_evidence,
            "component_observations": observations,
            "component_volatilities": volatilities,
            "eligibility_decisions": decision_values,
            "fx_evidence": fx_values,
            "market_dataset": market_dataset,
            "strategy_refs": strategy_values,
        }
    )
    return ValidatedConstructionEvidence(
        request=request,
        strategy_refs=strategy_values,
        eligibility_decisions=decision_values,
        account_snapshot=account_snapshot,
        market_dataset=market_dataset,
        analytics_evidence=analytics_evidence,
        fx_evidence=fx_values,
        component_volatilities=volatilities,
        component_observations=observations,
        evidence_hash=evidence_hash,
        strategy_lineage_hash=strategy_hash,
    )


def revalidate_activation_evidence(
    evidence: ValidatedConstructionEvidence,
    *,
    strategy_refs: Mapping[str, ValidatedStrategyRef],
    eligibility_decisions: Mapping[str, StrategyOperationalEligibilityDecision],
    now: datetime,
) -> None:
    """Revalidate exact mutable/expiring gates before activation.

    Args:
        evidence: Previously validated immutable evidence set.
        strategy_refs: Fresh component-keyed Strategy resolutions.
        eligibility_decisions: Fresh decision-ID-keyed Risk resolutions.
        now: Current injected UTC time.

    Raises:
        PortfolioError: If a reference changed or approval expired.
    """
    logger.info("Revalidating Portfolio activation evidence")
    current_refs, current_decisions = _validate_strategy_and_eligibility(
        evidence.request,
        strategy_refs,
        eligibility_decisions,
        now,
    )
    if _digest(current_refs) != evidence.strategy_lineage_hash or tuple(
        item.decision_id for item in current_decisions
    ) != tuple(item.decision_id for item in evidence.eligibility_decisions):
        raise PortfolioError("PORT_REFERENCE_CHANGED", "ACTIVATION_GATE")


__all__: tuple[str, ...] = (
    "ValidatedConstructionEvidence",
    "revalidate_activation_evidence",
    "validate_construction_evidence",
)
