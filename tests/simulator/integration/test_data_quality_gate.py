"""Workflow integration test for fail-closed market-data quality gating."""
# ruff: noqa: INP001

from pathlib import Path

import pytest
from app.services.simulator import SimulationError, run_backtest
from app.utils import logger
from tests.simulator.unit.test_orchestrator import (
    FakeDependencies,
    _auth,
    _dataset,
    _request,
)


def test_failed_data_quality_prevents_result_publication(tmp_path: Path) -> None:
    """Stop before engine output when Data quality status is failed."""
    logger.info("Testing WF-SIM-004 market-data quality gate")
    original = _dataset(f"req-{'e' * 64}")
    failed_quality = original.quality_report.model_copy(
        update={"quality_status": "failed"}
    )
    dataset = original.model_copy(update={"quality_report": failed_quality})
    request = _request(dataset, suffix="e")
    dependencies = FakeDependencies(tmp_path, dataset)
    with pytest.raises(SimulationError) as captured:
        run_backtest(request, _auth(request), dependencies)  # type: ignore[arg-type]
    assert captured.value.code == "SIM_DATA_SCHEMA_INVALID"
    assert not tuple(dependencies.artifact_root.rglob("manifest.json"))
