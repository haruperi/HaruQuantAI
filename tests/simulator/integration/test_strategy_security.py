"""Workflow integration test for the registered-strategy security boundary."""
# ruff: noqa: INP001

import pytest
from app.services.simulator import SimulationError
from app.services.simulator.validation import validate_run_inputs
from app.utils import logger
from tests.simulator.unit.test_validate import _valid_payload


def test_raw_strategy_code_is_rejected_before_execution() -> None:
    """Return a controlled code for raw source at the receiver boundary."""
    logger.info("Testing WF-SIM-006 registered-strategy-only enforcement")
    payload = _valid_payload() | {"source_code": "import os"}
    with pytest.raises(SimulationError) as captured:
        validate_run_inputs(payload)
    assert captured.value.code == "SIM_ARBITRARY_CODE_REJECTED"
