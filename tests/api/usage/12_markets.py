"""Database-configured MT5 usage evidence for Markets (FEAT-API-12)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import pandas as pd
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
from app.services.indicators import adr, rolling_volatility
from app.utils import generate_id, load_broker_provider_settings
from tqdm import tqdm

SYMBOLS = get_default_watchlist_symbols()
TIMEFRAME = "D1"


def _get_symbol_row(symbol: str) -> pd.Series | None:
    """Retrieve and compute market evidence row for one symbol."""
    request = build_market_data_request(
        source_id="mt5",
        symbol=symbol,
        data_kind="bars",
        timeframe=TIMEFRAME,
        limit=40,
        use_cache=False,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )
    response = get_market_data(request)

    snap_request = build_level1_snapshot_request(
        source_id="mt5", symbol=symbol, request_id=generate_id("req")
    )
    snap_response = get_level1_snapshot(snap_request)

    meta_request = build_symbol_metadata_request(
        source_id="mt5", symbol=symbol, request_id=generate_id("req")
    )
    meta_response = get_symbol_metadata(meta_request)

    if response.status != "success" or response.data is None:
        return None

    df = to_ohlcv_dataframe(response.data)

    vol_res = rolling_volatility(response.data, period=10, annualization_factor=252.0)
    if vol_res.data is not None and len(vol_res.data.output_columns) > 0:
        col_name = vol_res.data.output_columns[0]
        df["Volatility"] = vol_res.data.values[col_name].shift(1)  # noqa: PD011

    if (
        meta_response.status == "success"
        and meta_response.data is not None
        and getattr(meta_response.data, "pip_size", None) is not None
        and isinstance(meta_response.data.pip_size, (int, float, str))
    ):
        pip_size = float(meta_response.data.pip_size)
    else:
        return None

    adr_res = adr(response.data, period=10)
    if adr_res.data is not None and len(adr_res.data.output_columns) > 0:
        col_name = adr_res.data.output_columns[0]
        adr_raw_shifted = adr_res.data.values[col_name].shift(1)  # noqa: PD011
        df["ADR"] = (adr_raw_shifted / pip_size).round(1)
        range_pips = ((df["high"] - df["low"]) / pip_size).round(1)
        range_pct = (((df["high"] - df["low"]) / adr_raw_shifted) * 100.0).round(1)
        df["Range"] = range_pips.astype(str) + " (" + range_pct.astype(str) + "%)"

    df["Symbol"] = symbol
    df["Open"] = df["open"]
    df["High"] = df["high"]
    df["Low"] = df["low"]
    df["Last Price"] = ""
    df["Change"] = ""

    last_price = (
        float(snap_response.data.bid)
        if (
            snap_response.status == "success"
            and snap_response.data is not None
            and snap_response.data.bid is not None
        )
        else float(df["close"].iloc[-1])
    )

    today_open = float(df["open"].iloc[-1])
    pips = (last_price - today_open) / pip_size
    pct = ((last_price - today_open) / today_open) * 100.0
    change_str = f"{pips:+.1f} ({pct:+.2f}%)"

    df.loc[df.index[-1], "Last Price"] = f"{last_price:.5f}"
    df.loc[df.index[-1], "Change"] = change_str

    result_df = df[
        [
            "Symbol",
            "Last Price",
            "Change",
            "Volatility",
            "ADR",
            "Range",
            "Open",
            "High",
            "Low",
        ]
    ]

    return result_df.iloc[-1]


def main() -> None:
    """Retrieve the latest 40 D1 bars for default watchlist symbols and print evidence table."""

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
        rows = []
        for symbol in tqdm(SYMBOLS, desc="Fetching market data"):
            row = _get_symbol_row(symbol)
            if row is not None:
                rows.append(row)

        if rows:
            table_df = pd.DataFrame(rows).reset_index(drop=True)
            print("\n" + table_df.to_string(index=False))


if __name__ == "__main__":
    try:
        main()
    finally:
        close_data_provider_sessions()
        sys.exit(0)
