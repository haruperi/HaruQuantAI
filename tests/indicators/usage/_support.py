# ruff: noqa: E402
"""Shared response helpers for Indicators usage evidence."""

from __future__ import annotations

import os
import pathlib
import tempfile
from datetime import UTC, datetime, timedelta
from typing import Any, TypeVar

_data_dir = str(pathlib.Path(tempfile.gettempdir()) / "haruquant-data")
pathlib.Path(_data_dir).mkdir(exist_ok=True, parents=True)
os.environ.setdefault("DATA_DIR", _data_dir)
os.environ.setdefault("DATABASE_URL", "sqlite:///usage.db")
os.environ.setdefault("ENVIRONMENT", "dev")
os.environ.setdefault("WRITE_LOCK_LEASE_SECONDS", "30")
os.environ.setdefault("SQLITE_BUSY_TIMEOUT_SECONDS", "1")

from app.services.data import get_market_data, to_ohlcv_dataframe, unwrap_data_response
from app.services.indicators import get_indicator_result_values

_ResponseT = TypeVar("_ResponseT")
MarketDataset = Any
StandardResponse = Any
_MARKET_DATASET_CACHE: dict[str, MarketDataset] = {}


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
        from app.services.api import (
            build_system_broker_connection_config,
            get_api_settings,
            get_system_settings,
            run_api_migrations,
            store_system_credential,
            update_system_settings,
        )
        from app.services.api.composition.runtime_settings import (
            build_credential_key_set,
        )
        from app.services.data import (
            data_provider_connection_resolver_context,
            data_provider_settings_context,
            run_data_migrations,
        )
        from app.utils import generate_id, load_broker_provider_settings

        provider_settings = load_broker_provider_settings({"mt5_enabled": True})
        with data_provider_settings_context(provider_settings):
            req_id = generate_id("req")
            run_api_migrations(req_id)
            run_data_migrations(req_id)
            sys_settings = get_system_settings(request_id=req_id)
            if sys_settings.settings.get("MT5_ENABLED") != "true":
                update_system_settings(
                    actor_id="system",
                    settings={**sys_settings.settings, "MT5_ENABLED": "true"},
                    expected_version=sys_settings.version,
                    request_id=req_id,
                )
            try:
                mt5_config = build_system_broker_connection_config(
                    "mt5",
                    request_id=req_id,
                )
            except ValueError, KeyError, AttributeError, RuntimeError:
                api_settings = get_api_settings()
                key_set = build_credential_key_set(api_settings)
                store_system_credential(
                    "mt5",
                    {
                        "login": "123456",
                        "password": "password",
                        "server": "MetaQuotes-Demo",
                    },
                    key_set=key_set,
                    active_key_id=next(iter(key_set.keys())),
                    request_id=req_id,
                )
                mt5_config = build_system_broker_connection_config(
                    "mt5",
                    request_id=req_id,
                )
            with data_provider_connection_resolver_context(
                lambda broker_id, request_id: (
                    mt5_config
                    if broker_id == "mt5"
                    else build_system_broker_connection_config(
                        broker_id,
                        request_id=request_id,
                    )
                )
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
