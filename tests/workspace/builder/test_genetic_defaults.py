"""Unit tests for GeneticOptions defaults."""

from __future__ import annotations

import dataclasses

import pytest
from app.workspace.builder.genetic_defaults import (
    GeneticOptions,
)


class TestGeneticDefaults:
    """Test suite verifying GeneticOptionsDefaults creation and constraints."""

    def test_exact_defaults(self) -> None:
        """Verify exact field values for in_sample_type=7."""
        result = GeneticOptions.defaults(in_sample_type=7)
        expected = {
            "population_size": 5,
            "max_generations": 10,
            "crossover_probability": 50,
            "mutation_probability": 20,
            "show_advanced_settings": False,
            "islands": 10,
            "migration_modulo": 50,
            "migration_rate": 20,
            "init_generation_type": 1,
            "decimation_coef": 1,
            "evo_restart_on_finish": True,
            "evo_restart_on_stagnation": True,
            "evo_fitness_restart_type": 7,
            "evo_stagnation_generations": 30,
            "show_last_generation_databank": False,
            "fresh_blood_replace_similar": True,
            "fresh_blood_replace_weakest": True,
            "fresh_blood_weakest_pct": 10,
            "fresh_blood_weakest_generations": 2,
            "evo_training_validation_ratio": 50,
        }
        assert dataclasses.asdict(result) == expected

    def test_immutability(self) -> None:
        """Verify immutability, fresh instance creation, and type error guards."""
        res1 = GeneticOptions.defaults(in_sample_type=1)
        res2 = GeneticOptions.defaults(in_sample_type=1)

        assert res1 == res2
        assert res1 is not res2

        with pytest.raises(dataclasses.FrozenInstanceError):
            # Attempt mutation on frozen dataclass
            res1.population_size = 100  # type: ignore[misc]

        with pytest.raises(TypeError, match="in_sample_type must be an integer"):
            GeneticOptions.defaults(in_sample_type=True)  # bool is subclass of int

        with pytest.raises(TypeError, match="in_sample_type must be an integer"):
            GeneticOptions.defaults(in_sample_type="7")  # type: ignore[arg-type]
