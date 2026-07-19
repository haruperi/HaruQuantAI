"""Canonical hashes for Optimization parameter provenance."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from decimal import ROUND_HALF_EVEN, Decimal
from typing import TYPE_CHECKING

from app.utils import canonical_json, logger

if TYPE_CHECKING:
    from app.services.optimization.parameters.contracts import (
        ParameterSpace,
        ParameterValue,
    )

_MAX_DECIMAL_PLACES = 28


def _normalize(value: object, decimal_places: int) -> object:
    """Normalize decimals recursively for canonical hashing.

    Args:
        value: Candidate JSON-safe value.
        decimal_places: Decimal quantization precision.

    Returns:
        Canonical JSON-safe value.

    Raises:
        ValueError: If precision or a value is unsupported.
    """
    logger.debug("Normalizing Optimization hash material")
    if decimal_places < 0 or decimal_places > _MAX_DECIMAL_PLACES:
        raise ValueError("decimal_places must be between zero and 28")
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("hash decimals must be finite")
        quantum = Decimal(1).scaleb(-decimal_places)
        return format(value.quantize(quantum, rounding=ROUND_HALF_EVEN), "f")
    if isinstance(value, Mapping):
        return {key: _normalize(item, decimal_places) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return tuple(_normalize(item, decimal_places) for item in value)
    if value is None or isinstance(value, (bool, int, str)):
        return value
    raise ValueError("hash material contains an unsupported value")


def _digest(payload: object) -> str:
    """Return a SHA-256 digest for canonical material.

    Args:
        payload: Canonical JSON-safe material.

    Returns:
        Lowercase hexadecimal SHA-256 digest.
    """
    logger.debug("Hashing canonical Optimization material")
    return hashlib.sha256(canonical_json(payload).encode()).hexdigest()


def parameter_space_hash(space: ParameterSpace, *, decimal_places: int = 8) -> str:
    """Hash parameter definitions and constraints independent of input order.

    Args:
        space: Parameter-space contract.
        decimal_places: Decimal normalization precision.

    Returns:
        Lowercase SHA-256 digest.

    Raises:
        ValueError: If material cannot be normalized.
    """
    logger.info("Calculating Optimization parameter-space hash")
    rows = sorted(
        (item.model_dump(mode="python") for item in space.parameters),
        key=lambda item: str(item["name"]),
    )
    payload = {"parameters": rows, "constraints": sorted(space.constraints)}
    return _digest(_normalize(payload, decimal_places))


def candidate_hash(
    *,
    strategy_hash: str,
    data_hash: str,
    cost_model_hash: str,
    realism_hash: str,
    objective_hash: str,
    engine_type: str,
    engine_version: str,
    module_version: str,
    space_hash: str,
    executable_parameters: Mapping[str, ParameterValue],
    decimal_places: int = 8,
) -> str:
    """Hash complete execution provenance and active parameter values.

    Args:
        strategy_hash: Strategy configuration digest.
        data_hash: Dataset digest.
        cost_model_hash: Execution cost-model digest.
        realism_hash: Simulation realism digest.
        objective_hash: Objective policy digest.
        engine_type: Simulation engine type.
        engine_version: Simulation engine version.
        module_version: Optimization module version.
        space_hash: Parameter-space digest.
        executable_parameters: Active candidate values only.
        decimal_places: Decimal normalization precision.

    Returns:
        Lowercase SHA-256 candidate digest.

    Raises:
        ValueError: If provenance is blank or material is unsupported.
    """
    logger.info("Calculating Optimization candidate hash")
    provenance = {
        "strategy_hash": strategy_hash,
        "data_hash": data_hash,
        "cost_model_hash": cost_model_hash,
        "realism_hash": realism_hash,
        "objective_hash": objective_hash,
        "engine_type": engine_type,
        "engine_version": engine_version,
        "module_version": module_version,
        "space_hash": space_hash,
    }
    if any(not value or value != value.strip() for value in provenance.values()):
        raise ValueError("candidate provenance values must be non-empty and trimmed")
    payload = {**provenance, "parameters": dict(executable_parameters)}
    return _digest(_normalize(payload, decimal_places))


__all__ = ["candidate_hash", "parameter_space_hash"]
