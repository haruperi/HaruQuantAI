"""Tests for deterministic Phase 0 fixture generation."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pyarrow.parquet as pq

from scripts import generate_phase0_fixtures as fixtures


def test_generated_fixtures_have_expected_shapes(tmp_path: Path) -> None:
    """Generated files expose exact bounded schemas and record counts."""
    metadata = fixtures.generate(tmp_path)

    bars = pq.read_table(tmp_path / fixtures.FIXTURE_PATHS["FIX-BARS-M1-EURUSD"])
    ticks = pq.read_table(tmp_path / fixtures.FIXTURE_PATHS["FIX-TICKS-EURUSD"])
    assert bars.num_rows == metadata["FIX-BARS-M1-EURUSD"]["records"] == 1_440
    assert ticks.num_rows == metadata["FIX-TICKS-EURUSD"]["records"] == 3_600
    assert "close_scaled_1e5" in bars.column_names
    assert "ask_scaled_1e5" in ticks.column_names

    catalogue = tmp_path / fixtures.FIXTURE_PATHS["FIX-CATALOGUE-SQLITE"]
    with sqlite3.connect(catalogue) as connection:
        count = connection.execute("SELECT COUNT(*) FROM instruments").fetchone()
    assert count == (12,)


def test_generation_is_byte_deterministic(tmp_path: Path) -> None:
    """Two generations under the pinned runtime produce identical hashes."""
    first = fixtures.generate(tmp_path / "first")
    second = fixtures.generate(tmp_path / "second")

    assert {key: value["sha256"] for key, value in first.items()} == {
        key: value["sha256"] for key, value in second.items()
    }
