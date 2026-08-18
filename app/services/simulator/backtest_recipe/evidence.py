"""Retention of complete canonical backtest evidence (FEAT-SIM-19 seam).

The compact job projection is the only payload that may cross the HTTP
snapshot boundary, but terminal evidence — the full canonical Simulation
result and the full Analytics performance report — must survive job-registry
eviction. This module holds that evidence together and hands it to an
optional completion sink exactly once, after both owning domains have
succeeded.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from app.utils import get_logger

logger = get_logger(__name__)


class BacktestEvidencePersistenceError(Exception):
    """Raised when the completion sink cannot retain run evidence.

    The failure is reported to the caller as the stable code
    ``BACKTEST_EVIDENCE_PERSISTENCE_FAILED`` so a lost terminal outcome is
    never mistaken for a successful run.
    """

    def __init__(self) -> None:
        """Initialize the error with its stable persistence-failure code."""
        super().__init__("BACKTEST_EVIDENCE_PERSISTENCE_FAILED")


@dataclass(frozen=True, slots=True)
class BacktestRunEvidence:
    """Complete terminal evidence for one canonical backtest run.

    Attributes:
        projection: Compact JSON-safe run projection (the HTTP snapshot).
        simulation_result: Full canonical Simulation result owner object.
        performance_report: Full Analytics performance report owner object.
    """

    projection: Mapping[str, Any]
    simulation_result: Any
    performance_report: Any


type CompletionSink = Callable[[BacktestRunEvidence], None]


def sink_backtest_evidence(evidence: BacktestRunEvidence, sink: CompletionSink) -> None:
    """Hand complete run evidence to the sink exactly once.

    Args:
        evidence: Complete terminal evidence for one finished run.
        sink: Caller-supplied retention callable invoked once.

    Raises:
        BacktestEvidencePersistenceError: If the sink refuses or fails; the
            original cause is chained but never logged with its payload.
    """
    run_id = str(evidence.projection.get("run_id", ""))
    logger.info("Backtest evidence sink starting for run %s", run_id)
    try:
        sink(evidence)
    except Exception:  # noqa: BLE001 - sink refusal is the terminal outcome.
        logger.warning("Backtest evidence sink failed for run %s", run_id)
        raise BacktestEvidencePersistenceError from None
    logger.info("Backtest evidence sink succeeded for run %s", run_id)


__all__ = (
    "BacktestEvidencePersistenceError",
    "BacktestRunEvidence",
    "CompletionSink",
    "sink_backtest_evidence",
)
