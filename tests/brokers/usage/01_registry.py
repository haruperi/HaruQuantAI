"""Executable adapter registry and capability discovery examples."""

import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import _support  # noqa: F401
from _support import config
from app.services.brokers import (
    build_broker_margin_request,
    build_broker_profit_request,
    build_broker_value,
    create_broker_adapter,
    get_broker_capability_catalogue,
    get_broker_value_field,
    get_registered_brokers,
)


def _feature_header(title: str) -> None:
    """Print feature title and module flow banner."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'-' * 88}\n{title}\n{'-' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type and field/key signature."""
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


def fr_brokers_039_to_041_calculation_requests() -> None:
    """FR-BRK-039..041: Stage 1 — Provider-Native Calculation Requests."""
    _header("Stage 1: Config & Requests - Calculation Requests (FR-BRK-039..041)")
    margin_req = build_broker_margin_request(
        symbol="EURUSD",
        side="BUY",
        quantity="1.0",
        quantity_unit="lots",
        product_profile="mt5",
    )
    print(_format_result(margin_req))
    print(
        f"Data -> margin_symbol='{get_broker_value_field(margin_req, 'symbol')}', quantity='{get_broker_value_field(margin_req, 'quantity')}'"
    )

    profit_req = build_broker_profit_request(
        symbol="EURUSD",
        side="BUY",
        quantity="1.0",
        quantity_unit="lots",
        open_price="1.1000",
        close_price="1.1050",
        product_profile="mt5",
    )
    print(_format_result(profit_req))
    print(
        f"Data -> profit_symbol='{get_broker_value_field(profit_req, 'symbol')}', open='{get_broker_value_field(profit_req, 'open_price')}', close='{get_broker_value_field(profit_req, 'close_price')}'"
    )

    fee = build_broker_value(
        "fee_estimate", amount=Decimal("2.50"), currency_or_unit="USD"
    )
    print(_format_result(fee))
    print(
        f"Data -> fee_amount='{get_broker_value_field(fee, 'amount')}', unit='{get_broker_value_field(fee, 'currency_or_unit')}'"
    )


def fr_brokers_042_to_046_catalogue_discovery() -> None:
    """FR-BRK-042..046: Stage 2 — Catalogue Check and Capability Discovery."""
    _header("Stage 2: Catalogue Check - Capability Discovery (FR-BRK-042..046)")
    response = get_broker_capability_catalogue()
    assert response.status == "success"
    assert response.data is not None
    catalogue = response.data
    print(_format_result(catalogue))
    print(f"Data -> total_capabilities_count={len(catalogue)}")

    print(_format_result(get_registered_brokers))
    print(f"Data -> MarketDataProvider callable={callable(get_registered_brokers)}")

    print(_format_result(create_broker_adapter))
    print(f"Data -> AccountProvider callable={callable(create_broker_adapter)}")


def fr_brokers_047_explicit_lazy_creation() -> None:
    """FR-BRK-047: Stage 3 — Explicit Lazy Adapter Creation."""
    _header("Stage 3: Connected Adapter - Explicit Lazy Creation (FR-BRK-047)")
    response = get_registered_brokers()
    assert response.status == "success"
    assert response.data is not None
    brokers = response.data
    created = create_broker_adapter(brokers[0], config(brokers[0]))
    adapter = get_broker_value_field(created, "data")
    assert adapter is not None
    print(_format_result(adapter))
    print(f"Data -> created_adapter_type='{type(adapter).__name__}'")


def main() -> None:
    """Run adapter registry examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-BRK-01 — registry/ — Adapter Registry and Capability Discovery\n\n"
        "Purpose: Expose explicit lazy adapter resolution and a single static capability catalogue.\n\n"
        "Module flow:\n"
        "-> broker ID + config\n"
        "-> catalogue check\n"
        "-> explicit lazy creation\n"
        "-> connected adapter"
    )

    # Stage 1: Broker ID & config / calculation requests
    fr_brokers_039_to_041_calculation_requests()

    # Stage 2: Catalogue check and capability discovery
    fr_brokers_042_to_046_catalogue_discovery()

    # Stage 3: Explicit lazy creation & connected adapter output
    fr_brokers_047_explicit_lazy_creation()


if __name__ == "__main__":
    main()
