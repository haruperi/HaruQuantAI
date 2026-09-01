"""Shared response helpers for Indicators usage evidence."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Any, TypeVar

from app.services.data import get_market_data, to_ohlcv_dataframe, unwrap_data_response
from app.services.indicators import get_indicator_result_values

_ResponseT = TypeVar("_ResponseT")
MarketDataset = Any
StandardResponse = Any
_MARKET_DATASET_CACHE: dict[str, MarketDataset] = {}


def _build_persisted_mt5_config(request_id: str) -> object:
    """Resolve the authoritative database-backed MT5 configuration.

    Args:
        request_id: Canonical request identifier.

    Returns:
        Brokers-owned connection configuration.

    Raises:
        Exception: If persisted settings or credentials cannot be resolved.
    """
    from app.services.api import build_system_broker_connection_config

    return build_system_broker_connection_config("mt5", request_id=request_id)


def _resolve_mt5_usage_config(request_id: str) -> object:
    """Resolve genuine MT5 configuration or fail closed without fallback.

    Args:
        request_id: Canonical request identifier.

    Returns:
        Verified database-backed MT5 connection configuration.

    Raises:
        SystemExit: If the environment or persisted configuration is unavailable.
    """
    if os.environ.get("ENVIRONMENT", "").strip().casefold() != "dev":
        print("\nStatus: unavailable")
        print("\nMessage: genuine MT5 usage requires ENVIRONMENT=dev")
        print("\nData: None")
        raise SystemExit(3)
    try:
        return _build_persisted_mt5_config(request_id)
    except Exception as error:
        print("\nStatus: unavailable")
        print("\nMessage: persisted MT5 configuration is unavailable")
        print("\nData: None")
        raise SystemExit(3) from error


def _resolve_usage_connection_config(broker_id: str, request_id: str) -> object:
    """Resolve only the approved MT5 usage connection.

    Args:
        broker_id: Requested provider identifier.
        request_id: Canonical request identifier.

    Returns:
        Verified database-backed MT5 configuration.

    Raises:
        ValueError: If a provider other than MT5 is requested.
    """
    if broker_id != "mt5":
        raise ValueError("Indicators usage permits only the configured MT5 source")
    return _resolve_mt5_usage_config(request_id)


def get_mt5_usage_dataset(timeframe: str = "H1") -> MarketDataset:
    """Return the cached genuine EURUSD dataset for the last 100 days.

    Args:
        timeframe: Assigned timeframe (e.g. 'H1' or 'D1').

    Returns:
        Genuine normalized MT5 market data.

    Raises:
        SystemExit: If the configured MT5 source is unavailable.
        RuntimeError: If Data rejects the request for another reason.
    """
    cache_key = f"mt5_eurusd_{timeframe.lower()}_100d"
    if cache_key not in _MARKET_DATASET_CACHE:
        from app.composition.config import load_broker_provider_settings
        from app.kernel.identity import generate_id
        from app.services.data import (
            data_provider_connection_resolver_context,
            data_provider_settings_context,
        )

        req_id = generate_id("req")
        mt5_config = _resolve_mt5_usage_config(req_id)
        # Data's context-local enablement follows only after authoritative API
        # composition has verified the persisted provider flag and credential slot.
        provider_settings = load_broker_provider_settings({"mt5_enabled": True})
        with (
            data_provider_settings_context(provider_settings),
            data_provider_connection_resolver_context(
                lambda broker_id, request_id: (
                    mt5_config
                    if broker_id == "mt5"
                    else _resolve_usage_connection_config(broker_id, request_id)
                )
            ),
        ):
            end = datetime.now(UTC)
            start = end - timedelta(days=100)
            _MARKET_DATASET_CACHE[cache_key] = unwrap_market_data_response(
                get_market_data(
                    source_id="mt5",
                    symbol="EURUSD",
                    timeframe=timeframe,
                    start=start,
                    end=end,
                )
            )
    return _MARKET_DATASET_CACHE[cache_key]


def unwrap_indicator_response(response: StandardResponse[_ResponseT]) -> _ResponseT:
    """Print and return successful Indicators response data.

    Args:
        response: Indicators public response to display and unwrap.

    Returns:
        Successful response data.

    Raises:
        RuntimeError: If the response has no successful data.
    """
    try:
        data = response.data
        if (
            data is not None
            and hasattr(data, "indicator_id")
            and hasattr(data, "values")
        ):
            rendered = get_indicator_result_values(data)
        else:
            rendered = data
        print(f"\nStatus: {response.status}")
        print(f"\nMessage: {response.message}")
        print(f"\nData: {rendered}")
    except Exception as exc:
        print(f"\nError: {exc}")
        raise
    if response.status != "success" or data is None:
        failure = RuntimeError(response.message or "unknown indicator failure")
        print(f"\nError: {failure}")
        raise failure
    return data


def unwrap_market_data_response(
    response: StandardResponse[MarketDataset],
) -> MarketDataset:
    """Return Data's raw dataset while preserving DataError failures."""
    try:
        return unwrap_data_response(
            response,
            operation="indicators.usage.get_market_data",
            request_id=response.metadata.request_id,
        )
    except Exception as error:
        # Usage evidence is allowed to skip when its genuine external source is
        # unavailable; deterministic calculation failures must still surface.
        error_str = str(error)
        if (
            error_str
            in ("UNSUPPORTED_SOURCE", "SOURCE_UNAVAILABLE", "BROKER_CONNECTION_FAILED")
            or "SOURCE_UNAVAILABLE" in error_str
            or "BROKER_CONNECTION_FAILED" in error_str
        ):
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print("\nData: None")
            print(f"\nError: {error}")
            raise SystemExit(3) from error
        print(f"\nError: {error}")
        raise


def print_market_evidence(dataset: MarketDataset, *, rows: int = 8) -> None:
    """Print bounded genuine OHLCV rows and their source provenance."""
    frame = to_ohlcv_dataframe(dataset)
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
    "get_mt5_usage_dataset",
    "print_indicator_evidence",
    "print_market_evidence",
    "print_requirement_evidence",
    "unwrap_indicator_response",
    "unwrap_market_data_response",
]
