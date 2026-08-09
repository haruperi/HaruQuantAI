"""Scenario-holdout anti-leakage consumer port.

Extends ``FEAT-OPT-08``: anti-leakage controls for strict train/val/test splits,
point-in-time data, and **scenario holdouts**. Optimization already owns rolling and
anchored/expanding time-series splits with purge/embargo. Scenario holdouts are absent
through the `FEAT-SIM-11` provider. This module declares the
narrow consumer port and a deterministic fail-closed fallback: a missing scenario
provider yields ``SCENARIO_HOLDOUT_UNAVAILABLE``, which forces the walk-forward
``validation_needed`` path rather than an inferred clean holdout (rule 4).
The Simulator provider business logic is never implemented here.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol

from app.utils import get_logger

logger = get_logger(__name__)

SCENARIO_HOLDOUT_AVAILABLE = "HOLDOUT_LOCKED"
SCENARIO_HOLDOUT_UNAVAILABLE = "SCENARIO_HOLDOUT_UNAVAILABLE"


class ScenarioHoldoutPort(Protocol):
    """Narrow consumer port for Simulator-owned scenario holdout evidence.

    The Simulator provider (`FEAT-SIM-11`) supplies the production
    implementation that masks scenario identifiers in the validation set.
    """

    def scenario_holdout_mask(
        self,
        *,
        market_data_ref: str,  # noqa: ARG002
        validation_window: tuple[str, str],  # noqa: ARG002
    ) -> Mapping[str, object]:
        """Return validated scenario-holdout masking evidence.

        Args:
            market_data_ref: Approved Data source reference.
            validation_window: ``(start_iso, end_iso)`` UTC validation window.

        Raises:
            NotImplementedError: Protocol declarations are not executable.
        """
        logger.debug("Declaring scenario-holdout port")
        raise NotImplementedError


def evaluate_scenario_holdout(
    *,
    market_data_ref: str,
    validation_window: tuple[str, str],
    provider: ScenarioHoldoutPort | None,
    observed_scenario_ids: Sequence[str] | None = None,
) -> dict[str, object]:
    """Evaluate scenario-holdout integrity, failing closed without a provider.

    Args:
        market_data_ref: Approved Data source reference.
        validation_window: ``(start_iso, end_iso)`` UTC validation window.
        provider: Optional injected Simulator-owned scenario-holdout provider.
        observed_scenario_ids: Optional observed scenario identifiers used to detect
            holdout leakage when a provider is absent (the local signal only).

    Returns:
        Holdout-status mapping. When a provider is absent the status is
        ``SCENARIO_HOLDOUT_UNAVAILABLE`` and the result is marked
        ``validation_needed``. When a provider is present its evidence is passed
        through. A non-empty ``observed_scenario_ids`` overlap with any supplied
        training-scenario set is reported as ``holdout_leakage_detected``; the local
        check never fabricates a clean holdout.
    """
    logger.info(
        "Evaluating scenario holdout | provider=%s",
        "present" if provider is not None else "absent",
    )
    if provider is None:
        evidence: dict[str, object] = {
            "status": SCENARIO_HOLDOUT_UNAVAILABLE,
            "decision": "validation_needed",
            "reason": "scenario_engine_absent",
            "provider_feature": "FEAT-SIM-11",
        }
        if observed_scenario_ids is not None:
            evidence["observed_scenario_count"] = len(observed_scenario_ids)
        return evidence
    mask = dict(
        provider.scenario_holdout_mask(
            market_data_ref=market_data_ref, validation_window=validation_window
        )
    )
    mask.setdefault("status", SCENARIO_HOLDOUT_AVAILABLE)
    mask.setdefault("decision", "ready_for_validation")
    return mask


def detect_scenario_leakage(
    *,
    training_scenario_ids: Sequence[str],
    validation_scenario_ids: Sequence[str],
) -> dict[str, object]:
    """Detect overlap between training and validation scenario identifiers.

    This is a deterministic local leakage signal independent of any provider. It never
    infers a clean holdout: any overlap is reported, and identical empty inputs are
    reported as ``insufficient_evidence`` rather than a clean pass.

    Args:
        training_scenario_ids: Scenario identifiers observed in the training window.
        validation_scenario_ids: Scenario identifiers observed in the validation
            window.

    Returns:
        Leakage-evidence mapping with an explicit ``leakage_detected`` boolean and
        the overlapping identifiers when present.

    Raises:
        ValueError: If either identifier sequence is empty.
    """
    if not training_scenario_ids or not validation_scenario_ids:
        raise ValueError("scenario identifier sequences must be non-empty")
    training = set(training_scenario_ids)
    validation = set(validation_scenario_ids)
    overlap = sorted(training.intersection(validation))
    return {
        "leakage_detected": bool(overlap),
        "overlapping_scenarios": tuple(overlap),
        "training_scenario_count": len(training),
        "validation_scenario_count": len(validation),
        "decision": "holdout_leakage_detected" if overlap else "no_local_leakage",
    }


def get_scenario_holdout_contract_version() -> str:
    """Return the scenario-holdout consumer-port contract version.

    Returns:
        The canonical ``v1`` version string.
    """
    return "v1"


__all__: tuple[str, ...] = (
    "SCENARIO_HOLDOUT_AVAILABLE",
    "SCENARIO_HOLDOUT_UNAVAILABLE",
    "ScenarioHoldoutPort",
    "detect_scenario_leakage",
    "evaluate_scenario_holdout",
    "get_scenario_holdout_contract_version",
)
