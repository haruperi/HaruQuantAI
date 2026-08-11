"""Executable usage evidence for FEAT-INDI-08 order-flow indicators.

Only ``cumulative_volume_delta`` and ``aggressive_trade_imbalance`` are
demonstrated here — see ``app/services/indicators/order_flow/__init__.py``
for the documented reason the other seven spec ``IND-OF-*`` indicators are
not implemented against the current OHLCV-only ``MarketDataset`` contract.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.indicators import (
    aggressive_trade_imbalance,
    cumulative_volume_delta,
    get_indicator_result_values,
)
from tests.indicators.usage._support import (
    get_mt5_usage_dataset,
    print_indicator_evidence,
    print_market_evidence,
    print_requirement_evidence,
    unwrap_indicator_response,
)

MarketDataset = Any
_CACHE: dict[str, MarketDataset] = {}


def _feature_header(title: str) -> None:
    """Print the feature banner and module flow."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one section heading."""
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
        _CACHE["dataset"] = get_mt5_usage_dataset()
    return _CACHE["dataset"]


def fr_indi_062() -> None:
    """FR-INDI-062: Stage 1 — Calculate bar-sign cumulative volume delta.

    Documented OHLCV-derived approximation of spec ``IND-OF-03``; see
    ``order_flow/cumulative_volume_delta.py`` for the exact deviation from
    the canonical verified-aggressor-sign formula.
    """
    _header(
        "Stage 1: Order-flow pressure - cumulative_volume_delta execution (FR-INDI-062)"
    )
    result = unwrap_indicator_response(cumulative_volume_delta(_dataset(), window=5))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Cumulative-volume-delta calculations")
    print_requirement_evidence("FR-INDI-062", actual_data=values)


def fr_indi_063() -> None:
    """FR-INDI-063: Stage 2 — Calculate bar-sign aggressive trade imbalance.

    Documented OHLCV-derived approximation of spec ``IND-OF-04``; see
    ``order_flow/aggressive_trade_imbalance.py`` for the exact deviation
    from the canonical verified-aggressor-side formula.
    """
    _header(
        "Stage 2: Order-flow imbalance - aggressive_trade_imbalance execution "
        "(FR-INDI-063)"
    )
    result = unwrap_indicator_response(aggressive_trade_imbalance(_dataset(), window=5))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Aggressive-trade-imbalance calculations")
    print_requirement_evidence("FR-INDI-063", actual_data=values)


def main() -> None:
    """Run every order_flow requirement demonstration."""
    _feature_header(
        "FEATURE: FEAT-INDI-08 — order_flow/ — Signed Pressure and Book Change\n\n"
        "Purpose: Compute the two spec IND-OF-* indicators calculable from the\n"
        "current OHLCV-only MarketDataset contract, via stateless vectorized\n"
        "batch functions. The remaining seven IND-OF-* indicators require L2\n"
        "book/trade-event input this contract does not yet carry and are\n"
        "intentionally not registered (see order_flow/__init__.py).\n\n"
        "Module flow:\n"
        "-> normalized OHLC/volume values\n"
        "-> Core validation\n"
        "-> approved order_flow formula (bar-sign proxy)\n"
        "-> IndicatorResult"
    )

    try:
        _dataset()
    except RuntimeError as unavailable:
        print(
            f"Skipping order_flow examples: MT5 data unavailable ({unavailable.code})"
        )
        raise SystemExit(3) from None

    print_market_evidence(_dataset())
    fr_indi_062()
    fr_indi_063()


if __name__ == "__main__":
    main()
