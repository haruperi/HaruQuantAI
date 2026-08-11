"""Deterministic bounded input support for migrated formula examples."""

from __future__ import annotations

from app.services import indicators

from tests.indicators.usage._support import get_mt5_usage_dataset


def run_formula(operation: str, parameters: dict[str, object]) -> object:
    """Run and display one package-root formula with bounded OHLCV data."""
    try:
        response = getattr(indicators, operation)(get_mt5_usage_dataset(), **parameters)
        data = None
        if response.data is not None:
            data = indicators.get_indicator_result_values(response.data)
        print(f"\nStatus: {response.status}")
        print(f"\nMessage: {response.message}")
        print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")
        raise
    if response.status != "success" or response.data is None:
        failure = RuntimeError(response.message or "unknown indicator failure")
        print(f"\nError: {failure}")
        raise failure
    return response.data


def run_requirement(
    requirement_id: str,
    operation: str,
    parameters: dict[str, object],
) -> object:
    """Print one requirement success marker and its actual formula result.

    Args:
        requirement_id: Exact registered ``FR-INDI-NNN`` identifier.
        operation: Package-root Indicators operation name.
        parameters: Explicit operation keyword arguments.

    Returns:
        The calculated opaque Indicator result.
    """
    print(
        f"\n{'=' * 88}\n{requirement_id} {operation.replace('_', ' ').title()}\n{'=' * 88}"
    )
    result = run_formula(operation, parameters)
    print(f"SUCCESS: {requirement_id}")
    return result
