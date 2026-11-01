"""Genetic options settings service and validator.

Description:
    Manages the Genetic Options configuration tab in the Builder workspace,
    allowing customization and bounds validation of island topology, population size,
    generation counts, evolutionary reproduction probabilities (crossover and mutation),
    decimation, and fresh-blood insertion parameters.

Purpose:
    FEAT-BUILDER-GENETIC-OPTIONS: Service for creating and updating GP
    evolution options.

Key Capabilities:
    - FR-builder-genetic-options-default: Construct baseline settings delegating
      to GeneticOptions.
    - FR-builder-genetic-options-validate: Validate updated parameters against
      numeric bounds and return a new immutable GeneticOptionsDefaults
      instance.

Python API Usage:
    from app.workspace.builder.settings_genetic_options import (
        SettingsGeneticOptionsService,
    )
    service = SettingsGeneticOptionsService()
    defaults = service.create_default(in_sample_type=1)

CLI Usage:
    python -c "from app.workspace.builder.settings_genetic_options import (
        SettingsGeneticOptionsService,
    ); print(1)"
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.workspace.builder.genetic_defaults import (
    GeneticOptions,
    GeneticOptionsDefaults,
)

logger = get_logger(__name__)

_MIN_POPULATION_SIZE: int = 1
_MIN_MAX_GENERATIONS: int = 1
_MIN_PROBABILITY: int = 0
_MAX_PROBABILITY: int = 100
_MIN_ISLANDS: int = 1
_MIN_DECIMATION: int = 1
_MIN_VALIDATION_RATIO: int = 1
_MAX_VALIDATION_RATIO: int = 99


class SettingsGeneticOptionsService:
    """Service managing genetic algorithm parameters and update validation."""

    def create_default(self, *, in_sample_type: int = 1) -> GeneticOptionsDefaults:
        """Create baseline genetic options for a specified in-sample type.

        Args:
            in_sample_type: Identifier of the in-sample type.

        Returns:
            GeneticOptionsDefaults populated with baseline values.
        """
        logger.debug(
            "Creating default genetic options with in_sample_type=%d", in_sample_type
        )
        return GeneticOptions.defaults(in_sample_type=in_sample_type)

    def validate_and_update(
        self,
        current: GeneticOptionsDefaults,
        updates: Mapping[str, Any],
    ) -> GeneticOptionsDefaults:
        """Validate and apply dictionary of updates to GeneticOptionsDefaults.

        Args:
            current: The existing GeneticOptionsDefaults instance.
            updates: Mapping of field names to proposed new values.

        Returns:
            A new GeneticOptionsDefaults instance with updates applied.

        Raises:
            DomainError: If any parameter value falls outside valid operational bounds.
        """
        logger.debug(
            "Validating and applying genetic options updates: %s", list(updates.keys())
        )
        data = dataclasses.asdict(current)

        for key, val in updates.items():
            if key not in data:
                raise DomainError(
                    code="BUILDER_INVALID_GENETIC_OPTIONS",
                    message=f"Unknown genetic options parameter: {key}",
                )
            data[key] = val

        pop_size = data.get("population_size", 0)
        max_gen = data.get("max_generations", 0)
        crossover_prob = data.get("crossover_probability", -1)
        mutation_prob = data.get("mutation_probability", -1)
        islands = data.get("islands", 0)
        decimation = data.get("decimation_coef", 0)
        ratio = data.get("evo_training_validation_ratio", 0)

        if not (isinstance(pop_size, int) and pop_size >= _MIN_POPULATION_SIZE):
            raise DomainError(
                code="BUILDER_INVALID_GENETIC_OPTIONS",
                message=f"population_size must be an integer >= 1 (got {pop_size})",
            )
        if not (isinstance(max_gen, int) and max_gen >= _MIN_MAX_GENERATIONS):
            raise DomainError(
                code="BUILDER_INVALID_GENETIC_OPTIONS",
                message=f"max_generations must be an integer >= 1 (got {max_gen})",
            )
        if not (
            isinstance(crossover_prob, int)
            and _MIN_PROBABILITY <= crossover_prob <= _MAX_PROBABILITY
        ):
            raise DomainError(
                code="BUILDER_INVALID_GENETIC_OPTIONS",
                message=(
                    f"crossover_probability must be in [0, 100] (got {crossover_prob})"
                ),
            )
        if not (
            isinstance(mutation_prob, int)
            and _MIN_PROBABILITY <= mutation_prob <= _MAX_PROBABILITY
        ):
            raise DomainError(
                code="BUILDER_INVALID_GENETIC_OPTIONS",
                message=(
                    f"mutation_probability must be in [0, 100] (got {mutation_prob})"
                ),
            )
        if not (isinstance(islands, int) and islands >= _MIN_ISLANDS):
            raise DomainError(
                code="BUILDER_INVALID_GENETIC_OPTIONS",
                message=f"islands must be an integer >= 1 (got {islands})",
            )
        if not (isinstance(decimation, int) and decimation >= _MIN_DECIMATION):
            raise DomainError(
                code="BUILDER_INVALID_GENETIC_OPTIONS",
                message=f"decimation_coef must be an integer >= 1 (got {decimation})",
            )
        if not (
            isinstance(ratio, int)
            and _MIN_VALIDATION_RATIO <= ratio <= _MAX_VALIDATION_RATIO
        ):
            raise DomainError(
                code="BUILDER_INVALID_GENETIC_OPTIONS",
                message=(
                    f"evo_training_validation_ratio must be in [1, 99] (got {ratio})"
                ),
            )

        return GeneticOptionsDefaults(**data)
