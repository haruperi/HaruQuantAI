"""Genuine MT5 usage evidence for the Data API feature (FEAT-DATA-01).

The workstation ``data`` gateway (``app/services/api/widgets/data``) is a
thin transport boundary: it authenticates and delegates every market-data read
to the Data domain public API (``app.services.data``), which drives the
configured broker adapter for the ``mt5`` source. This standalone program
follows that delegation path exactly as it is composed in the API backend, same
as ``tests/api/usage/12_markets.py``, fetching a bounded set of real MT5 D1 bars
and printing the evidence table.

It degrades gracefully: when no MT5 terminal is available, business data is
never invented and a bounded message is printed.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.composition.config import load_broker_provider_settings
from app.kernel.identity import generate_id
from app.services.api import (
    build_system_broker_connection_config,
    get_default_watchlist_symbols,
    get_system_settings,
)
from app.services.data import (
    build_level1_snapshot_request,
    build_market_data_request,
    build_symbol_metadata_request,
    close_data_provider_sessions,
    data_provider_connection_resolver_context,
    data_provider_settings_context,
    get_level1_snapshot,
    get_market_data,
    get_symbol_metadata,
    to_ohlcv_dataframe,
)

# Keep the evidence bounded: only the first few default watchlist symbols.
SYMBOLS = tuple(get_default_watchlist_symbols())[:1]
TIMEFRAME = "M1"


def _fetch_symbol_rows(symbol: str) -> tuple[object, object, object]:
    """Fetch one symbol's real MT5 bars, snapshot, and metadata together.

    Args:
        symbol: Broker-native MT5 symbol to retrieve.

    Returns:
        A ``(bars_response, snapshot_response, metadata_response)`` triple of
        Data-owned standard responses.
    """
    bars_request = build_market_data_request(
        source_id="mt5",
        symbol=symbol,
        data_kind="bars",
        timeframe=TIMEFRAME,
        limit=10000,
        use_cache=False,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )
    snap_request = build_level1_snapshot_request(
        source_id="mt5", symbol=symbol, request_id=generate_id("req")
    )
    meta_request = build_symbol_metadata_request(
        source_id="mt5", symbol=symbol, request_id=generate_id("req")
    )
    return (
        get_market_data(bars_request),
        get_level1_snapshot(snap_request),
        get_symbol_metadata(meta_request),
    )


def main() -> None:
    """Retrieve real MT5 D1 bars for bounded default watchlist symbols."""
    system_record = get_system_settings(request_id=generate_id("req"))
    provider_fields = {
        "MT5_ENABLED": "mt5_enabled",
        "MT5_TERMINAL_PATH": "mt5_terminal_path",
    }
    explicit_values = {
        field: system_record.settings[key]
        for key, field in provider_fields.items()
        if key in system_record.settings
    }
    provider_settings = load_broker_provider_settings(explicit_values)
    mt5_config = build_system_broker_connection_config(
        "mt5", request_id=generate_id("req")
    )

    with (
        data_provider_settings_context(provider_settings),
        data_provider_connection_resolver_context(
            lambda broker_id, request_id: (
                mt5_config
                if broker_id == "mt5"
                else build_system_broker_connection_config(
                    broker_id, request_id=request_id
                )
            )
        ),
    ):
        for symbol in SYMBOLS:
            bars_response, snap_response, meta_response = _fetch_symbol_rows(symbol)
            if bars_response.status != "success" or bars_response.data is None:
                print(
                    f"{symbol}: MT5 source unavailable "
                    "(no real data fabricated; is the MT5 terminal running?)"
                )
                continue

            frame = to_ohlcv_dataframe(bars_response.data)
            last_close = float(frame["close"].iloc[-1])
            row_count = len(frame)

            bid = (
                snap_response.data.bid
                if (
                    snap_response.status == "success"
                    and snap_response.data is not None
                    and snap_response.data.bid is not None
                )
                else None
            )
            point = (
                meta_response.data.point
                if (
                    meta_response.status == "success"
                    and meta_response.data is not None
                    and getattr(meta_response.data, "point", None) is not None
                )
                else None
            )
            print(
                f"{symbol}: {row_count} {TIMEFRAME} bars, last close {last_close:.5f}"
            )
            if bid is not None:
                print(f"  real snapshot bid: {float(bid):.5f}")
            if point is not None:
                print(f"  point size: {float(point)}")
            # print(frame.tail(5).to_string(index=False))
            print(frame)


if __name__ == "__main__":
    try:
        print("Starting MT5 usage evidence retrieval...")
        start_time = time.time()
        main()
        end_time = time.time()
        print(f"Completed in {end_time - start_time:.2f} seconds.")
        # Results of previously tested runs:
        # 1 000 000 bars 127 seconds
        # 100 000 bars 14 seconds
        # 10 000 bars 3 seconds

    finally:
        close_data_provider_sessions()
        sys.exit(0)
