"""Executable usage evidence for volume indicators."""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import get_market_data
from app.services.indicators import (
    build_liquidity_snapshot,
    cmf,
    get_indicator_result_values,
    measure_order_flow,
    mfi,
    obv,
    parse_liquidity_snapshot,
    price_volume_distribution,
)
from tests.indicators.usage._support import (
    print_indicator_evidence,
    print_market_evidence,
    print_requirement_evidence,
    unwrap_indicator_response,
    unwrap_market_data_response,
)

MarketDataset = Any
_CACHE: dict[str, MarketDataset] = {}


def _feature_header(title: str) -> None:
    """Print the feature banner and module flow."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _dataset() -> MarketDataset:
    """Return one cached real read-only market dataset."""

    if "dataset" not in _CACHE:
        _CACHE["dataset"] = unwrap_market_data_response(
            get_market_data(
                source_id="mt5",
                symbol="EURUSD",
                timeframe="M5",
                limit=20,
            )
        )
    return _CACHE["dataset"]


def fr_indi_027() -> None:
    """FR-INDI-027: Stage 1 — Calculate CMF using approved money-flow formula."""
    _header("Stage 1: Volume flow contract - CMF formula execution (FR-INDI-027)")
    result = unwrap_indicator_response(cmf(_dataset(), period=2))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="CMF calculations")
    print_requirement_evidence("FR-INDI-027", actual_data=values)


def fr_indi_028() -> None:
    """FR-INDI-028: Stage 2 — Calculate OBV with cumulative volume contract."""
    _header("Stage 2: Cumulative volume contract - OBV formula execution (FR-INDI-028)")
    result = unwrap_indicator_response(obv(_dataset()))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="OBV calculations")
    print_requirement_evidence("FR-INDI-028", actual_data=values)


def fr_indi_029() -> None:
    """FR-INDI-029: Stage 3 — Calculate MFI using official flow weighting."""
    _header("Stage 3: Flow oscillator contract - MFI formula execution (FR-INDI-029)")
    result = unwrap_indicator_response(mfi(_dataset(), period=2))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="MFI calculations")
    print_requirement_evidence("FR-INDI-029", actual_data=values)


def fr_indi_030() -> None:
    """FR-INDI-030: Stage 4 — Calculate price-volume distribution profile."""
    _header(
        "Stage 4: Volume distribution contract - price_volume_distribution execution (FR-INDI-030)"
    )
    result = unwrap_indicator_response(
        price_volume_distribution(_dataset(), period=2, bins=2)
    )
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Price-volume distribution calculations")
    print_requirement_evidence("FR-INDI-030", actual_data=values)


def main() -> None:
    """Run every volume requirement demonstration."""
    _feature_header(
        "FEATURE: FEAT-INDI-06 — volume/ — Volume-Flow and Price-Volume Calculation\n\n"
        "Purpose: Compute deterministic volume-confirmation and rolling volume-by-price "
        "features from normalized OHLCV bars.\n\n"
        "Module flow:\n"
        "-> normalized OHLCV bars + config\n"
        "-> Core validation\n"
        "-> approved volume-flow formula\n"
        "-> IndicatorResult"
    )

    try:
        _dataset()
    except RuntimeError as unavailable:
        print(f"Skipping volume examples: MT5 data unavailable ({unavailable.code})")
        raise SystemExit(3) from None

    print_market_evidence(_dataset())
    fr_indi_027()
    fr_indi_028()
    fr_indi_029()
    fr_indi_030()
    order_flow = measure_order_flow(
        bid_depth=120.0,
        ask_depth=100.0,
        previous_bid_depth=110.0,
        previous_ask_depth=105.0,
        aggressive_buy_volume=60.0,
        aggressive_sell_volume=40.0,
        sweep_threshold=0.7,
    )
    snapshot = build_liquidity_snapshot(
        observed_at=_dataset().records[-1].available_at,
        spread=0.0002,
        executable_depth=220.0,
        imbalance=float(order_flow.data["imbalance"]),
        volume=float(_dataset().records[-1].volume),
        fill_probability=None,
        regime="NORMAL",
        complete=False,
    )
    parsed = parse_liquidity_snapshot(snapshot.data)
    print(f"Order-flow DATA: {order_flow.data}")
    print(f"Liquidity-snapshot DATA: {parsed.data}")


if __name__ == "__main__":
    main()
