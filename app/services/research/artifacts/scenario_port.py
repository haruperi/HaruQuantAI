"""Research consumer port for `FEAT-SIM-11` scenario evidence.

Research consumes an injected Simulator-owned provider. This module implements
only the consumer port and a fail-closed fallback: a
missing Simulator provider returns ``UNAVAILABLE`` and the caller degrades
safely. No Simulator provider business logic is implemented here (change-
control rule 3).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from app.utils import get_logger

logger = get_logger(__name__)

# Consumer port signature: a Simulator provider, when wired at integration
# (Phase 14), returns a validated scenario-evidence mapping for a scenario
# identity. Research never implements the provider's logic.
ScenarioEvidenceProvider = Callable[[str], Mapping[str, object] | None]


def build_scenario_evidence_port(
    provider: ScenarioEvidenceProvider | None = None,
) -> Callable[[str], str]:
    """Return a scenario-evidence consumer with a fail-closed fallback.

    Args:
        provider: Optional Simulator-owned scenario-evidence provider. When
            ``None`` (the deferred-integration default), every lookup fails
            closed to ``UNAVAILABLE``.

    Returns:
        Consumer callable mapping a scenario identity to an availability label.
    """

    def _consumer(scenario_id: str) -> str:
        """Return scenario-evidence availability for one scenario identity.

        Args:
            scenario_id: Scenario identity to look up.

        Returns:
            ``AVAILABLE`` when the provider returns evidence, otherwise
            ``UNAVAILABLE`` (fail-closed fallback).
        """
        if provider is None:
            logger.info(
                "Scenario-evidence provider unavailable; returning UNAVAILABLE for %s",
                scenario_id,
            )
            return "UNAVAILABLE"
        try:
            evidence = provider(scenario_id)
        except RuntimeError, TypeError, ValueError:
            logger.warning("Scenario-evidence provider failed; returning UNAVAILABLE")
            return "UNAVAILABLE"
        return "AVAILABLE" if evidence is not None else "UNAVAILABLE"

    return _consumer


__all__ = (
    "ScenarioEvidenceProvider",
    "build_scenario_evidence_port",
)
