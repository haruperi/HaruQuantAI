"""Deterministic Portfolio construction service."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from app.services.portfolio.construction.methods import (
    WeightRow,
    equal_weights,
    fixed_weights,
    inverse_volatility_weights,
)
from app.services.portfolio.contracts import (
    PortfolioComponentWeight,
    PortfolioConstructionResult,
)
from app.services.portfolio.exceptions import PortfolioError
from app.utils import canonical_json, logger

if TYPE_CHECKING:
    from app.services.portfolio.config import PortfolioSettings
    from app.services.portfolio.evidence import ValidatedConstructionEvidence


def _digest(value: object) -> str:
    """Hash supported canonical construction material.

    Args:
        value: Supported canonical material.

    Returns:
        Lowercase SHA-256 digest.
    """
    logger.debug("Hashing deterministic Portfolio construction material")
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class ConstructionService:
    """Construct bounded candidates from previously validated evidence."""

    def __init__(self, settings: PortfolioSettings) -> None:
        """Initialize construction with complete explicit settings.

        Args:
            settings: Validated Portfolio settings.
        """
        logger.info("Initializing Portfolio construction service")
        self._settings = settings

    def _calculate(
        self, evidence: ValidatedConstructionEvidence
    ) -> tuple[WeightRow, ...]:
        """Select exactly one approved construction method.

        Args:
            evidence: Validated immutable construction evidence.

        Returns:
            Ordered calculated weight rows.

        Raises:
            PortfolioError: If the method or evidence is unsupported.
        """
        logger.info("Selecting approved Portfolio construction method")
        request = evidence.request
        common = {
            "minimum": self._settings.portfolio_min_weight,
            "maximum": self._settings.portfolio_max_weight,
        }
        if request.method == "fixed":
            return fixed_weights(
                request.fixed_weights,
                tolerance=self._settings.portfolio_weight_sum_tolerance,
                **common,
            )
        if request.method == "equal":
            return equal_weights(
                tuple(component.component_id for component in request.components),
                **common,
            )
        if request.method == "inverse_volatility":
            return inverse_volatility_weights(
                evidence.component_volatilities,
                evidence.component_observations,
                minimum_observations=(
                    self._settings.portfolio_min_evidence_observations
                ),
                **common,
            )
        raise PortfolioError("PORT_METHOD_UNSUPPORTED", "METHOD")

    def construct(
        self,
        evidence: ValidatedConstructionEvidence,
        *,
        created_at: datetime,
    ) -> PortfolioConstructionResult:
        """Produce one complete immutable construction result or publish nothing.

        Args:
            evidence: Validated immutable evidence set.
            created_at: Injected aware UTC publication time.

        Returns:
            Complete deterministic construction result.

        Raises:
            PortfolioError: If time, count, method, or weights are invalid.
        """
        logger.info("Constructing deterministic Portfolio allocation candidate")
        if created_at.tzinfo is None or created_at.utcoffset() != timedelta(0):
            raise PortfolioError("PORT_INVALID_INPUT", "CREATED_AT_NOT_UTC")
        request = evidence.request
        if len(request.components) > self._settings.portfolio_max_strategies:
            raise PortfolioError("PORT_CONSTRUCTION_FAILED", "MAX_STRATEGIES")
        calculated = self._calculate(evidence)
        references = {item.component_id: item for item in request.components}
        weights = tuple(
            PortfolioComponentWeight(
                component_id=component_id,
                strategy_id=references[component_id].strategy_id,
                strategy_version=references[component_id].strategy_version,
                capital_weight=capital,
                proposed_risk_budget_weight=proposed,
            )
            for component_id, capital, proposed in calculated
        )
        config_hash = _digest(self._settings.model_dump(mode="json"))
        identity_material = {
            "component_weights": tuple(
                item.model_dump(mode="json") for item in weights
            ),
            "config_hash": config_hash,
            "created_at": created_at,
            "evidence_hash": evidence.evidence_hash,
            "method": request.method,
            "portfolio_id": request.portfolio_id,
            "portfolio_version": request.portfolio_version,
            "scope": dict(request.scope),
            "strategy_lineage_hash": evidence.strategy_lineage_hash,
            "trace": {
                "causation_id": request.causation_id,
                "correlation_id": request.correlation_id,
                "request_id": request.request_id,
                "workflow_id": request.workflow_id,
            },
        }
        canonical_hash = _digest(identity_material)
        return PortfolioConstructionResult(
            result_id=f"portfolio-result-{canonical_hash[:32]}",
            portfolio_id=request.portfolio_id,
            portfolio_version=request.portfolio_version,
            scope=request.scope,
            status="constructed",
            component_weights=weights,
            method=request.method,
            config_hash=config_hash,
            evidence_hash=evidence.evidence_hash,
            strategy_lineage_hash=evidence.strategy_lineage_hash,
            canonical_hash=canonical_hash,
            created_at=created_at,
            request_id=request.request_id,
            workflow_id=request.workflow_id,
            correlation_id=request.correlation_id,
            causation_id=request.causation_id,
        )


__all__: tuple[str, ...] = ("ConstructionService",)
