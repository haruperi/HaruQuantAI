"""Unit tests for the GridTest application plugin service and models.

Description:
    Tests GridTestService, plugin descriptors, row generation parity, and
    non-silent requirement logging.

Purpose:
    FEAT-GRID-TEST: Verify backend service and model parity for Grid Test.
"""

import logging

import pytest
from app.workspace.grid_test.app_grid_test import GridTestService
from app.workspace.grid_test.app_grid_test_models import (
    GridTestIntervalsModel,
    GridTestPluginDescriptor,
    GridTestRowModel,
)


def test_grid_test_plugin_descriptor(caplog: pytest.LogCaptureFixture) -> None:
    """Verify plugin descriptor metadata matches donor specification."""
    with caplog.at_level(logging.INFO):
        service = GridTestService()
        descriptor = service.get_plugin_descriptor()

    assert descriptor.name == "GridTest"
    assert descriptor.app_code == "GRIDTEST"
    assert descriptor.category == "App"
    assert descriptor.product == "SQUANT"
    assert descriptor.preferred_position == 10
    assert descriptor.context_path == "/gridtest"
    assert descriptor.tooltip == "Grid test"
    assert descriptor.hidden is True
    assert "FR-GRID-TEST-PLUGIN-REGISTRATION" in caplog.text


def test_grid_test_intervals(caplog: pytest.LogCaptureFixture) -> None:
    """Verify timer interval metadata conforms to donor periods."""
    service = GridTestService()
    with caplog.at_level(logging.INFO):
        intervals = service.get_intervals()

    assert intervals.add == 20
    assert intervals.remove == 30
    assert intervals.change == 40
    assert intervals.count == 50
    assert "FR-GRID-TEST-INTERVALS" in caplog.text


def test_grid_test_manual_batch(caplog: pytest.LogCaptureFixture) -> None:
    """Verify manual batch generation yields 100 deterministic rows."""
    service = GridTestService()
    with caplog.at_level(logging.INFO):
        batch = service.generate_manual_batch()

    assert batch.total_count == 100
    assert len(batch.rows) == 100

    # Boundary checks
    first = batch.rows[0]
    assert first.index == 0
    assert first.value == 0
    assert first.text == "0-text"

    last = batch.rows[99]
    assert last.index == 99
    assert last.value == 198
    assert last.text == "99-text"

    assert "FR-GRID-TEST-ROW-PARITY" in caplog.text


def test_grid_test_timed_row(caplog: pytest.LogCaptureFixture) -> None:
    """Verify single timed row generation for arbitrary counter."""
    service = GridTestService()
    with caplog.at_level(logging.INFO):
        row = service.generate_timed_row(42)

    assert row.index == 42
    assert row.value == 84
    assert row.text == "42-text"
    assert "FR-GRID-TEST-ROW-PARITY" in caplog.text


def test_grid_test_models_instantiation() -> None:
    """Verify direct Pydantic model instantiations and field validations."""
    row = GridTestRowModel(index=5, value=10, text="5-text")
    assert row.index == 5
    assert row.value == 10
    assert row.text == "5-text"

    custom_intervals = GridTestIntervalsModel(add=25, remove=35, change=45, count=55)
    assert custom_intervals.add == 25

    custom_descriptor = GridTestPluginDescriptor(name="CustomGridTest")
    assert custom_descriptor.name == "CustomGridTest"
    assert custom_descriptor.app_code == "GRIDTEST"
