"""Workflow integration test for fail-closed market-data quality gating."""

import asyncio
from pathlib import Path

import pytest
from app.composition.logging import get_logger
from app.services.simulator import (
    run_backtest_async,
    unwrap_simulation_response,
)

from tests.simulator.component.test_orchestrator import (
    FakeDependencies,
    _auth,
    _dataset,
    _request,
)

logger = get_logger(__name__)


def test_rejected_data_quality_prevents_result_publication(tmp_path: Path) -> None:
    """Stop before engine output when Data quality is rejected."""
    logger.info("Testing WF-SIM-004 market-data quality gate")
    original = _dataset("req-eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee")
    failed_quality = original.quality_report.model_copy(
        update={
            "quality_status": "critical",
            "quality_decision": "rejected",
            "quality_score": 0,
        }
    )
    dataset = original.model_copy(update={"quality_report": failed_quality})
    request = _request(dataset, suffix="e")
    dependencies = FakeDependencies(tmp_path, dataset)
    with pytest.raises(Exception, match="quality") as captured:
        unwrap_simulation_response(
            asyncio.run(run_backtest_async(request, _auth(request), dependencies)),
            operation="test.data_quality.run_backtest",
        )
    assert captured.value.code == "SIM_DATA_SCHEMA_INVALID"
    assert not tuple(dependencies.artifact_root.rglob("manifest.json"))
