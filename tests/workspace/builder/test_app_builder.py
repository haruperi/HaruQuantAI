"""Unit tests for AppBuilderService and workspace state transitions."""

from __future__ import annotations

from app.workspace.builder.app_builder import AppBuilderService
from app.workspace.builder.genetic_defaults import GeneticOptionsDefaults
from app.workspace.builder.settings_what_to_build import WhatToBuildSettings


def test_golden_fixture_state_lifecycle() -> None:
    """Verify golden fixture: initialization seeds defaults and transitions start->pause->resume->stop."""
    service = AppBuilderService()

    # Initial state
    resp = service.get_state("proj_1")
    assert resp.data.project_id == "proj_1"
    assert resp.data.status == "IDLE"
    assert resp.data.genetic_options.evo_fitness_restart_type == 1
    assert resp.data.genetic_options.population_size == 5

    # Start
    start_resp = service.start("proj_1")
    assert start_resp.data.status == "RUNNING"
    assert start_resp.data.generated_count > 0

    # Pause
    pause_resp = service.pause("proj_1")
    assert pause_resp.data.status == "PAUSED"

    # Resume
    resume_resp = service.resume("proj_1")
    assert resume_resp.data.status == "RUNNING"

    # Stop
    stop_resp = service.stop("proj_1")
    assert stop_resp.data.status == "STOPPED"


def test_save_settings() -> None:
    """Verify updating and persisting Builder workspace settings."""
    service = AppBuilderService()
    custom_wtb = WhatToBuildSettings(build_mode="RANDOM", min_entry_conditions=2)
    custom_gen = GeneticOptionsDefaults(population_size=20, islands=2)

    save_resp = service.save_settings(
        "proj_custom",
        what_to_build=custom_wtb,
        genetic_options=custom_gen,
    )

    assert save_resp.data.what_to_build.build_mode == "RANDOM"
    assert save_resp.data.what_to_build.min_entry_conditions == 2
    assert save_resp.data.genetic_options.population_size == 20
    assert save_resp.data.to_dict()["status"] == "IDLE"
