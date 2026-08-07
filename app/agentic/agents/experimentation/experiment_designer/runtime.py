"""Durable relational implementation of the experiment-ledger port."""

from __future__ import annotations

from datetime import datetime
from typing import cast

from pydantic import BaseModel

from app.agentic.agents.experimentation.experiment_designer.schemas import (
    ExperimentSpec,
    ExperimentVerdict,
)
from app.agentic.persistence import (
    create_agentic_persistence_store,
    create_experiment_holdout_use,
    create_experiment_run,
    create_experiment_spec,
    create_experiment_verdict,
    read_experiment_holdout_use,
    read_experiment_runs,
    read_experiment_spec,
    read_experiment_verdict,
)


def _encode(value: object) -> str:
    """Encode one validated experiment contract.

    Returns:
        JSON text.

    Raises:
        TypeError: If the value is not a validated model.
    """
    if not isinstance(value, BaseModel):
        raise TypeError("Agentic experiment state must be a validated model")
    return value.model_dump_json()


class _DurableExperimentStore:
    """Data-backed implementation of the experiment-ledger port."""

    def __init__(self) -> None:
        """Build the relational persistence handle."""
        self._store = create_agentic_persistence_store(
            {
                "experiment-spec": (_encode, ExperimentSpec.model_validate_json),
                "experiment-verdict": (
                    _encode,
                    ExperimentVerdict.model_validate_json,
                ),
            }
        )

    def save_spec(self, spec: ExperimentSpec) -> ExperimentSpec:
        """Persist one pre-registered protocol.

        Returns:
            Persisted protocol.

        Raises:
            ValueError: If the digest is already bound to different content.
        """
        existing = self.load_spec(spec.spec_hash)
        if existing is not None:
            if existing != spec:
                raise ValueError("Experiment specification digest conflict")
            return existing
        create_experiment_spec(self._store, spec)
        return spec

    def load_spec(self, spec_hash: str) -> ExperimentSpec | None:
        """Load one protocol by digest.

        Returns:
            Persisted protocol or ``None``.
        """
        return cast(
            "ExperimentSpec | None",
            read_experiment_spec(self._store, spec_hash),
        )

    def record_run(
        self,
        spec_hash: str,
        run_id: str,
        evidence_class: str,
        lineage: dict[str, str],
        at_time: datetime,
    ) -> None:
        """Record one receiver-returned run against a protocol.

        Raises:
            ValueError: If the protocol was not pre-registered.
        """
        spec = self.load_spec(spec_hash)
        if spec is None:
            raise ValueError("Experiment run requires a pre-registered protocol")
        create_experiment_run(
            spec_hash=spec_hash,
            run_id=run_id,
            evidence_class=evidence_class,
            lineage={**lineage, "task_id": spec.task_id},
            at_time=at_time,
        )

    def list_runs(self, spec_hash: str) -> tuple[dict[str, str], ...]:
        """List receiver lineage for one protocol.

        Returns:
            Ordered detached run rows.
        """
        return read_experiment_runs(spec_hash, 1_000)

    def reserve_holdout(
        self,
        spec_hash: str,
        task_id: str,
        run_id: str,
        at_time: datetime,
    ) -> bool:
        """Atomically claim the single permitted holdout use.

        Returns:
            Whether this call obtained the unique reservation.
        """
        return create_experiment_holdout_use(
            spec_hash=spec_hash,
            task_id=task_id,
            run_id=run_id,
            consumed_at=at_time,
        )

    def holdout_spent(self, spec_hash: str) -> bool:
        """Report whether the protocol has consumed holdout.

        Returns:
            Whether a reservation exists.
        """
        return read_experiment_holdout_use(spec_hash)

    def save_verdict(self, verdict: ExperimentVerdict) -> ExperimentVerdict:
        """Persist one immutable experiment verdict.

        Returns:
            Persisted verdict.

        Raises:
            ValueError: If the verdict identity already exists.
        """
        existing = read_experiment_verdict(self._store, verdict.verdict_id)
        if existing is not None:
            raise ValueError("Experiment verdict identity already exists")
        create_experiment_verdict(self._store, verdict)
        return verdict


def build_durable_experiment_store() -> object:
    """Build the canonical durable experiment-ledger implementation.

    Returns:
        Opaque store satisfying the internal experiment-ledger port.
    """
    return _DurableExperimentStore()


__all__ = ("build_durable_experiment_store",)
