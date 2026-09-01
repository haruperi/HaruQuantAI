"""Experiment-ledger persistence port and its deterministic in-memory double.

Agentic declares the port; a composition root binds the durable implementation
Data owns. Following the Portfolio and Risk precedents, no domain outside Data
implements a database writer, so this module holds a Protocol and an in-memory
double only.

`reserve_holdout` is the enforcement point for holdout scarcity: it succeeds
once per pre-registered protocol digest and refuses every later attempt, so a
second look at holdout cannot be recorded and therefore is not performed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.composition.logging import get_logger

if TYPE_CHECKING:
    from datetime import datetime

    from app.agentic.agents.experimentation.experiment_designer.schemas import (
        ExperimentSpec,
        ExperimentVerdict,
    )

logger = get_logger(__name__)


@runtime_checkable
class AgenticExperimentStore(Protocol):
    """Durable experiment ledger for protocols, runs, holdout use, and verdicts."""

    def save_spec(self, spec: ExperimentSpec) -> ExperimentSpec:
        """Persist one pre-registered protocol.

        Args:
            spec: Validated immutable protocol.

        Returns:
            The persisted protocol.
        """
        ...

    def load_spec(self, spec_hash: str) -> ExperimentSpec | None:
        """Load one protocol by its pre-registration digest.

        Args:
            spec_hash: Pre-registration digest.

        Returns:
            The protocol, or None when unrecorded.
        """
        ...

    def record_run(
        self,
        spec_hash: str,
        run_id: str,
        evidence_class: str,
        lineage: dict[str, str],
        at_time: datetime,
    ) -> None:
        """Record one executed run against a protocol.

        Args:
            spec_hash: Pre-registration digest of the protocol.
            run_id: Receiver-returned run identity.
            evidence_class: Evidence class this run represents.
            lineage: Receiver-returned reproducibility references.
            at_time: Record time.
        """
        ...

    def list_runs(self, spec_hash: str) -> tuple[dict[str, str], ...]:
        """List every run recorded against a protocol.

        Args:
            spec_hash: Pre-registration digest of the protocol.

        Returns:
            Ordered recorded run rows.
        """
        ...

    def reserve_holdout(
        self,
        spec_hash: str,
        task_id: str,
        run_id: str,
        at_time: datetime,
    ) -> bool:
        """Claim the single permitted holdout use for one protocol.

        Args:
            spec_hash: Pre-registration digest of the protocol.
            task_id: Owning task identity.
            run_id: Run about to consume holdout.
            at_time: Consumption time.

        Returns:
            True when this call claimed holdout, False when already spent.
        """
        ...

    def holdout_spent(self, spec_hash: str) -> bool:
        """Report whether a protocol's holdout has already been consumed.

        Args:
            spec_hash: Pre-registration digest of the protocol.

        Returns:
            True when holdout is already spent.
        """
        ...

    def save_verdict(self, verdict: ExperimentVerdict) -> ExperimentVerdict:
        """Persist one run-bound verdict.

        Args:
            verdict: Validated immutable verdict.

        Returns:
            The persisted verdict.
        """
        ...


class _InMemoryExperimentStore:
    """Deterministic in-process experiment ledger for tests and usage."""

    def __init__(self) -> None:
        """Initialize the empty ledger."""
        self._specs: dict[str, ExperimentSpec] = {}
        self._runs: list[dict[str, str]] = []
        self._holdout: dict[str, dict[str, str]] = {}
        self._verdicts: dict[str, ExperimentVerdict] = {}

    def save_spec(self, spec: ExperimentSpec) -> ExperimentSpec:
        """Persist one pre-registered protocol.

        Args:
            spec: Validated immutable protocol.

        Returns:
            The persisted protocol.

        Raises:
            ValueError: If a different protocol already claims the digest.
        """
        existing = self._specs.get(spec.spec_hash)
        if existing is not None and existing.spec_id != spec.spec_id:
            message = f"experiment protocol digest {spec.spec_hash} already recorded"
            raise ValueError(message)
        self._specs[spec.spec_hash] = spec
        return spec

    def load_spec(self, spec_hash: str) -> ExperimentSpec | None:
        """Load one protocol by its pre-registration digest.

        Args:
            spec_hash: Pre-registration digest.

        Returns:
            The protocol, or None when unrecorded.
        """
        return self._specs.get(spec_hash)

    def record_run(
        self,
        spec_hash: str,
        run_id: str,
        evidence_class: str,
        lineage: dict[str, str],
        at_time: datetime,
    ) -> None:
        """Record one executed run against a protocol.

        Args:
            spec_hash: Pre-registration digest of the protocol.
            run_id: Receiver-returned run identity.
            evidence_class: Evidence class this run represents.
            lineage: Receiver-returned reproducibility references.
            at_time: Record time.
        """
        self._runs.append(
            {
                **lineage,
                "spec_hash": spec_hash,
                "run_id": run_id,
                "evidence_class": evidence_class,
                "created_at": at_time.isoformat(),
            },
        )

    def list_runs(self, spec_hash: str) -> tuple[dict[str, str], ...]:
        """List every run recorded against a protocol.

        Args:
            spec_hash: Pre-registration digest of the protocol.

        Returns:
            Ordered recorded run rows.
        """
        return tuple(row for row in self._runs if row["spec_hash"] == spec_hash)

    def reserve_holdout(
        self,
        spec_hash: str,
        task_id: str,
        run_id: str,
        at_time: datetime,
    ) -> bool:
        """Claim the single permitted holdout use for one protocol.

        Args:
            spec_hash: Pre-registration digest of the protocol.
            task_id: Owning task identity.
            run_id: Run about to consume holdout.
            at_time: Consumption time.

        Returns:
            True when this call claimed holdout, False when already spent.
        """
        if spec_hash in self._holdout:
            logger.warning(
                "Holdout for protocol %s was already consumed by run %s",
                spec_hash,
                self._holdout[spec_hash]["run_id"],
            )
            return False
        self._holdout[spec_hash] = {
            "task_id": task_id,
            "run_id": run_id,
            "consumed_at": at_time.isoformat(),
        }
        return True

    def holdout_spent(self, spec_hash: str) -> bool:
        """Report whether a protocol's holdout has already been consumed.

        Args:
            spec_hash: Pre-registration digest of the protocol.

        Returns:
            True when holdout is already spent.
        """
        return spec_hash in self._holdout

    def save_verdict(self, verdict: ExperimentVerdict) -> ExperimentVerdict:
        """Persist one run-bound verdict.

        Args:
            verdict: Validated immutable verdict.

        Returns:
            The persisted verdict.

        Raises:
            ValueError: If the verdict identity already exists.
        """
        if verdict.verdict_id in self._verdicts:
            message = f"experiment verdict {verdict.verdict_id} already exists"
            raise ValueError(message)
        self._verdicts[verdict.verdict_id] = verdict
        return verdict


def build_in_memory_experiment_store() -> AgenticExperimentStore:
    """Build the deterministic in-process experiment ledger.

    Returns:
        A store satisfying `AgenticExperimentStore`.
    """
    logger.debug("Building the in-memory Agentic experiment store")
    return _InMemoryExperimentStore()
