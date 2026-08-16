"""WF-OPT-001 request packaging integration."""

# ruff: noqa: INP001
import asyncio

from app.services.optimization import (
    run_parameter_sweep,
    run_robustness_analysis,
)
from app.utils import get_logger
from tests.optimization.unit.test_robustness_contracts import monte_carlo_request
from tests.optimization.unit.test_search_contracts import search_request
from tests.optimization.unit.test_sweep import FakeAdapter

logger = get_logger(__name__)


def test_optimization_and_robustness_requests_return_typed_evidence() -> None:
    """Both public request forms return their versioned result contracts."""
    logger.debug("Testing WF-OPT-001 request packaging")
    optimization = asyncio.run(run_parameter_sweep(search_request(), FakeAdapter()))
    robustness = run_robustness_analysis(monte_carlo_request(), max_simulations=5)
    assert optimization.data is not None
    assert robustness.data is not None
    assert optimization.data.schema_id == "optimization.result.v1"
    assert robustness.data.schema_id == "optimization.robustness.v1"
