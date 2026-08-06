"""Unit test configuration and latency ceiling enforcement."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import pytest

_ = (np, pd)

if TYPE_CHECKING:
    from collections.abc import Generator

_MAX_UNIT_CALL_SECONDS = 0.100


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item,
    call: pytest.CallInfo[None],
) -> Generator[None, pytest.TestReport]:
    """Fail an Indicators unit test whose call phase exceeds 100 milliseconds.

    Args:
        item: Collected pytest unit-test item.
        call: Execution information for the current test phase.

    Yields:
        Control to pytest's report construction.

    Returns:
        The completed pytest report through the hook wrapper.
    """
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.duration > _MAX_UNIT_CALL_SECONDS:
        report.outcome = "failed"
        report.longrepr = (
            f"Unit test {item.nodeid} exceeded the call-phase latency ceiling: "
            f"{report.duration * 1000:.2f} ms > "
            f"{_MAX_UNIT_CALL_SECONDS * 1000:.2f} ms"
        )
