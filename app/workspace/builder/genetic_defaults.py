"""Genetic options default configuration model and factory.

Description:
    Constructs the observed baseline configuration for genetic programming (GP)
    evolution runs within the Builder workspace, specifying population dimensions,
    island topologies, crossover/mutation probabilities, restart conditions,
    and fresh-blood injection parameters.

Purpose:
    FEAT-BUILDER-GENETIC-DEFAULTS: Provide typed baseline parameters for GP evolution.

Key Capabilities:
    - FR-builder-genetic-defaults: Frozen dataclass instantiation with exact
      scalar default values.
    - FR-builder-type-guard: Type check ensuring in_sample_type is strictly an int.

Python API Usage:
    from app.workspace.builder.genetic_defaults import GeneticOptions
    defaults = GeneticOptions.defaults(in_sample_type=1)

CLI Usage:
    python -c "from app.workspace.builder.genetic_defaults import (
        GeneticOptions,
    ); print(GeneticOptions.defaults(in_sample_type=1))"
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.host.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class GeneticOptionsDefaults:
    """Frozen dataclass representing default genetic options."""

    population_size: int = 5
    max_generations: int = 10
    crossover_probability: int = 50
    mutation_probability: int = 20
    show_advanced_settings: bool = False
    islands: int = 10
    migration_modulo: int = 50
    migration_rate: int = 20
    init_generation_type: int = 1
    decimation_coef: int = 1
    evo_restart_on_finish: bool = True
    evo_restart_on_stagnation: bool = True
    evo_fitness_restart_type: int = 1
    evo_stagnation_generations: int = 30
    show_last_generation_databank: bool = False
    fresh_blood_replace_similar: bool = True
    fresh_blood_replace_weakest: bool = True
    fresh_blood_weakest_pct: int = 10
    fresh_blood_weakest_generations: int = 2
    evo_training_validation_ratio: int = 50


class GeneticOptions:
    """Factory helper for genetic options defaults."""

    @classmethod
    def defaults(cls, *, in_sample_type: int) -> GeneticOptionsDefaults:
        """Construct default genetic options for a given in-sample type.

        Args:
            in_sample_type: Integer identifier for in-sample evaluation type.

        Returns:
            GeneticOptionsDefaults populated with baseline values.

        Raises:
            TypeError: If in_sample_type is not an integer.
        """
        if type(in_sample_type) is not int:
            raise TypeError("in_sample_type must be an integer")

        logger.debug(
            "Constructing GeneticOptionsDefaults with in_sample_type=%d",
            in_sample_type,
        )
        return GeneticOptionsDefaults(evo_fitness_restart_type=in_sample_type)
