"""Failure-path tests for canonical Optimization result recovery."""

import pytest
from app.services.optimization import (
    build_optimization_evidence,
    load_optimization_result,
)
from app.services.optimization.contracts import OptimizationError

from tests.optimization.unit.test_evidence_contracts import evidence_request


class _ReadStore:
    """Minimal result-read store fixture."""

    def __init__(self, value: object = None, *, fail: bool = False) -> None:
        self.value = value
        self.fail = fail

    def load_result(self, search_id: str) -> object:
        """Return configured evidence or raise a store failure."""
        del search_id
        if self.fail:
            raise RuntimeError("database unavailable")
        return self.value


def test_result_read_handles_absence_failure_and_identity_conflict() -> None:
    """Fail closed on store errors and conflicting persisted identity."""
    assert (
        load_optimization_result(
            search_id="search-missing",
            reproducibility_hash="",
            store=_ReadStore(),  # type: ignore[arg-type]
        )
        is None
    )
    with pytest.raises(OptimizationError, match="RESULT_READ_FAILED"):
        load_optimization_result(
            search_id="search-one",
            reproducibility_hash="",
            store=_ReadStore(fail=True),  # type: ignore[arg-type]
        )

    result = build_optimization_evidence(evidence_request())
    with pytest.raises(OptimizationError, match="RESULT_IDENTITY_MISMATCH"):
        load_optimization_result(
            search_id="search-conflict",
            reproducibility_hash=result.reproducibility_hash,
            store=_ReadStore(result),  # type: ignore[arg-type]
        )
    with pytest.raises(OptimizationError, match="RESULT_IDENTITY_MISMATCH"):
        load_optimization_result(
            search_id=result.search_id,
            reproducibility_hash="f" * 64,
            store=_ReadStore(result),  # type: ignore[arg-type]
        )
