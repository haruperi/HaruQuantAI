"""Unit tests for SettingsGeneticOptions service."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.workspace.builder.settings_genetic_options import SettingsGeneticOptionsService


def test_create_default() -> None:
    """Ensure create_default delegates to GeneticOptions.defaults."""
    service = SettingsGeneticOptionsService()
    defaults = service.create_default(in_sample_type=1)
    assert defaults.population_size == 5
    assert defaults.evo_fitness_restart_type == 1


def test_validate_and_update_golden_fixture() -> None:
    """Ensure updating population_size and islands preserves other fields."""
    service = SettingsGeneticOptionsService()
    defaults = service.create_default(in_sample_type=1)

    updated = service.validate_and_update(
        defaults, {"population_size": 50, "islands": 4}
    )
    assert updated.population_size == 50
    assert updated.islands == 4
    assert updated.max_generations == defaults.max_generations
    assert updated.crossover_probability == defaults.crossover_probability
    assert updated.evo_fitness_restart_type == 1


def test_invalid_bounds_raise() -> None:
    """Ensure invalid bounds raise BUILDER_INVALID_GENETIC_OPTIONS."""
    service = SettingsGeneticOptionsService()
    defaults = service.create_default(in_sample_type=1)

    # Crossover > 100
    with pytest.raises(DomainError) as exc:
        service.validate_and_update(defaults, {"crossover_probability": 120})
    assert exc.value.code == "BUILDER_INVALID_GENETIC_OPTIONS"

    # Population < 1
    with pytest.raises(DomainError) as exc:
        service.validate_and_update(defaults, {"population_size": 0})
    assert exc.value.code == "BUILDER_INVALID_GENETIC_OPTIONS"

    # Islands < 1
    with pytest.raises(DomainError) as exc:
        service.validate_and_update(defaults, {"islands": 0})
    assert exc.value.code == "BUILDER_INVALID_GENETIC_OPTIONS"

    # Decimation < 1
    with pytest.raises(DomainError) as exc:
        service.validate_and_update(defaults, {"decimation_coef": 0})
    assert exc.value.code == "BUILDER_INVALID_GENETIC_OPTIONS"

    # Ratio outside 1..99
    with pytest.raises(DomainError) as exc:
        service.validate_and_update(defaults, {"evo_training_validation_ratio": 100})
    assert exc.value.code == "BUILDER_INVALID_GENETIC_OPTIONS"

    # Unknown parameter
    with pytest.raises(DomainError) as exc:
        service.validate_and_update(defaults, {"non_existent_key": 42})
    assert exc.value.code == "BUILDER_INVALID_GENETIC_OPTIONS"
