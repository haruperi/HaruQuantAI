"""Workflow integration test for the registered-strategy security boundary."""

import pytest
from app.composition.logging import get_logger
from app.services.simulator import (
    unwrap_simulation_response,
    validate_run_inputs,
)

from tests.simulator.unit.test_validate import _valid_payload

logger = get_logger(__name__)


def test_raw_strategy_code_is_rejected_before_execution() -> None:
    """Return a controlled code for raw source at the receiver boundary."""
    logger.info("Testing WF-SIM-006 registered-strategy-only enforcement")
    payload = _valid_payload() | {"source_code": "import os"}
    with pytest.raises(Exception, match="Raw code or path") as captured:
        unwrap_simulation_response(
            validate_run_inputs(payload), operation="test.strategy.validate_run_inputs"
        )
    assert captured.value.code == "SIM_ARBITRARY_CODE_REJECTED"
