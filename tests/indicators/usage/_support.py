# ruff: noqa: E402
"""Shared response helpers for Indicators usage evidence."""

from __future__ import annotations

import os
import pathlib
import tempfile
from typing import Any, TypeVar

_data_dir = str(pathlib.Path(tempfile.gettempdir()) / "haruquant-data")
pathlib.Path(_data_dir).mkdir(exist_ok=True, parents=True)
os.environ.setdefault("DATA_DIR", _data_dir)
os.environ.setdefault("DATABASE_URL", "sqlite:///usage.db")
os.environ.setdefault("ENVIRONMENT", "dev")
os.environ.setdefault("WRITE_LOCK_LEASE_SECONDS", "30")
os.environ.setdefault("SQLITE_BUSY_TIMEOUT_SECONDS", "1")

from app.services.data import to_ohlcv_dataframe, unwrap_data_response
from app.services.indicators import get_indicator_result_values

_ResponseT = TypeVar("_ResponseT")
MarketDataset = Any
StandardResponse = Any


def unwrap_indicator_response(response: StandardResponse[_ResponseT]) -> _ResponseT:
    """Return successful Indicators data or fail with its safe error message."""
    if response.status != "success" or response.data is None:
        detail = response.message or "unknown indicator failure"
        raise RuntimeError(detail)
    return response.data


def unwrap_market_data_response(
    response: StandardResponse[MarketDataset],
) -> MarketDataset:
    """Return Data's raw dataset while preserving DataError failures."""
    return unwrap_data_response(
        response,
        operation="indicators.usage.get_market_data",
        request_id=response.metadata.request_id,
    )


def print_market_evidence(dataset: MarketDataset, *, rows: int = 8) -> None:
    """Print bounded genuine OHLCV rows and their source provenance."""
    response = to_ohlcv_dataframe(dataset)
    frame = unwrap_data_response(
        response,
        operation="indicators.usage.to_ohlcv_dataframe",
        request_id=response.metadata.request_id,
    )
    provider = dataset.source_metadata.get(
        "source_id",
        dataset.source_metadata.get("provider", "unknown"),
    )
    print(
        f"Genuine input ({provider}, {dataset.symbol} {dataset.timeframe}, "
        f"{dataset.record_count} rows):"
    )
    print(frame.tail(rows).to_string())


def print_indicator_evidence(
    result: object,
    *,
    label: str = "Calculated indicator rows",
    rows: int = 8,
) -> None:
    """Print bounded calculated values with availability and quality evidence."""
    print(f"{label}:")
    print(get_indicator_result_values(result).tail(rows).to_string())


def print_requirement_evidence(
    requirement_id: str,
    *,
    actual_data: object,
) -> None:
    """Print bounded success and result evidence for one requirement.

    Args:
        requirement_id: Registered Indicators functional requirement ID.
        actual_data: Genuine data returned by the demonstrated operation.

    Returns:
        None.

    Raises:
        ValueError: If requirement_id is not an FR-INDI-NNN identifier.
    """
    import re

    import pandas as pd

    if not re.match(r"^FR-INDI-\d{3}$", requirement_id):
        raise ValueError(
            f"Requirement ID must match FR-INDI-NNN, got: {requirement_id}"
        )

    print(f"SUCCESS: {requirement_id}")

    if isinstance(actual_data, (pd.DataFrame, pd.Series)):
        rendered = actual_data.tail(8).to_string()
    elif isinstance(actual_data, (list, tuple)):
        rendered = str(actual_data[-8:])
    elif isinstance(actual_data, dict):
        rendered = str(actual_data)
    else:
        rendered = str(actual_data)

    if len(rendered) > 2000:
        rendered = rendered[:1997] + "..."

    print(f"DATA: {rendered}")


__all__ = [
    "print_indicator_evidence",
    "print_market_evidence",
    "print_requirement_evidence",
    "unwrap_indicator_response",
    "unwrap_market_data_response",
]
