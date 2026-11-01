"""Unit tests for TaskBuildRunner and execution pipeline."""

from __future__ import annotations

from app.workspace.builder.genetic_defaults import GeneticOptionsDefaults
from app.workspace.builder.settings_blocks import (
    BlocksSelectionSettings,
    BuildingBlockSelection,
)
from app.workspace.builder.settings_parts_to_improve import PartsToImproveSettings
from app.workspace.builder.settings_rankings import RankingsSettings
from app.workspace.builder.settings_what_to_build import WhatToBuildSettings
from app.workspace.builder.task_build import BarRecord, TaskBuildRunner


def test_golden_fixture_deterministic_execution() -> None:
    """Verify golden fixture: pop_size=4, max_gen=2, seed=42 evaluates 8 candidates."""
    genetic_options = GeneticOptionsDefaults(
        population_size=4,
        max_generations=2,
        islands=1,
    )
    what_to_build = WhatToBuildSettings(build_mode="GENETIC")
    blocks = BlocksSelectionSettings()
    parts = PartsToImproveSettings()
    rankings = RankingsSettings(target_databank="Results", max_records=100)

    summary = TaskBuildRunner.execute(
        project_id="proj_1",
        what_to_build=what_to_build,
        genetic_options=genetic_options,
        blocks=blocks,
        parts_to_improve=parts,
        rankings=rankings,
        seed=42,
    )

    assert summary.candidates_evaluated == 8
    assert summary.generations_completed == 2
    assert summary.build_mode == "GENETIC"
    assert summary.candidates_accepted + summary.candidates_rejected == 8
    assert len(summary.accepted_strategy_ids) == summary.candidates_accepted
    assert summary.to_dict()["candidates_evaluated"] == 8


def test_calibrate_indicators() -> None:
    """Verify indicator calibration computes output boundaries."""
    blocks = BlocksSelectionSettings(
        selections=(
            BuildingBlockSelection(
                block_id="indicator.rsi", category="INDICATORS", enabled=True
            ),
            BuildingBlockSelection(
                block_id="indicator.ema", category="INDICATORS", enabled=True
            ),
            BuildingBlockSelection(
                block_id="indicator.cci", category="INDICATORS", enabled=True
            ),
        )
    )
    bars = [
        BarRecord(time=1000, open=1.1000, high=1.1050, low=1.0980, close=1.1020),
        BarRecord(time=2000, open=1.1020, high=1.1080, low=1.1010, close=1.1070),
    ]

    ranges = TaskBuildRunner.calibrate_indicators(blocks, bars)
    assert "indicator.rsi" in ranges
    assert ranges["indicator.rsi"] == (0.0, 100.0)
    assert ranges["indicator.cci"] == (-200.0, 200.0)
    assert "indicator.ema" in ranges
    assert ranges["indicator.ema"][0] <= ranges["indicator.ema"][1]
