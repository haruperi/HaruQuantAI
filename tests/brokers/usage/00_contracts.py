"""Executable canonical-contract examples."""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import _support  # noqa: F401
from app.services.brokers import (
    build_broker_connection_config,
    build_broker_order_filter,
    build_broker_order_modification_request,
    build_broker_order_request,
    build_broker_position_close_request,
    build_broker_position_filter,
    build_broker_position_modification_request,
    build_broker_value,
    get_broker_value_field,
    get_registered_brokers,
)

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


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


def fr_brokers_001_to_005_enums_and_interpretation() -> None:
    """FR-BRK-001..005: Stage 1 — Enums & Canonical Interpretation."""
    _header(
        "Stage 1: Enums & Interpretation - Provider IDs & Canonical Enums (FR-BRK-001..005)"
    )
    for name in ("mt5", "ctrader", "binance_spot"):
        cfg = build_broker_connection_config(name, "sandbox", provider_enabled=True)
        broker_id = get_broker_value_field(cfg, "broker_id")
        print(_format_result(cfg))
        print(f"Data -> provider_id='{broker_id}'")

    err = build_broker_value(
        "error",
        code="BROKER_UNKNOWN_OUTCOME",
        message="bounded",
        retryable=False,
    )
    print(_format_result(err))
    print(f"Data -> error_code='{get_broker_value_field(err, 'code')}'")


def fr_brokers_006_to_038_models_and_dtos() -> None:
    """FR-BRK-006..038: Stage 2 — Structural DTOs and Data Construction."""
    _header("Stage 2: Models & DTOs - Canonical Structural Schemas (FR-BRK-006..038)")
    reg_response = get_registered_brokers()
    print(_format_result(reg_response))
    print(f"Data -> status='{get_broker_value_field(reg_response, 'status')}'")

    page = build_broker_value("page", items=("bounded",), limit=1, truncated=False)
    print(_format_result(page))
    print(f"Data -> page_items_count={len(get_broker_value_field(page, 'items'))}")

    conn_status = build_broker_value(
        "connection_status",
        state="disconnected",
        transport_connected=False,
        environment="demo",
        session_generation=0,
        observed_at=_NOW,
    )
    print(_format_result(conn_status))
    print(f"Data -> connection_state='{get_broker_value_field(conn_status, 'state')}'")

    acct_info = build_broker_value(
        "account_info",
        account_id="10001",
        account_reference_redacted="***001",
        currency="USD",
        balance=Decimal(1000),
        retrieved_at=_NOW,
    )
    print(_format_result(acct_info))
    print(
        f"Data -> account_id='{get_broker_value_field(acct_info, 'account_id')}', currency='{get_broker_value_field(acct_info, 'currency')}'"
    )


def fr_brokers_033_to_038_mutation_requests() -> None:
    """FR-BRK-033..038: Stage 3 — Bounded Mutation & Filter Request Envelopes."""
    _header(
        "Stage 3: Protocols & Standard Response - Mutation & Filter Contracts (FR-BRK-033..038)"
    )
    order_req = build_broker_order_request(
        "EURUSD", "BUY", "MARKET", "0.01", "lots", "demo"
    )
    print(_format_result(order_req))
    print(
        f"Data -> order_request_symbol='{get_broker_value_field(order_req, 'symbol')}'"
    )

    mod_req = build_broker_order_modification_request("o1", limit_price="1.11")
    print(_format_result(mod_req))
    print(
        f"Data -> modification_order_id='{get_broker_value_field(mod_req, 'order_id')}'"
    )

    pos_mod = build_broker_position_modification_request("p1", stop_loss="1.09")
    print(_format_result(pos_mod))
    print(
        f"Data -> position_modification_id='{get_broker_value_field(pos_mod, 'position_id')}'"
    )

    pos_close = build_broker_position_close_request("p1", "0.5", "lots")
    print(_format_result(pos_close))
    print(
        f"Data -> position_close_id='{get_broker_value_field(pos_close, 'position_id')}'"
    )

    order_filter = build_broker_order_filter("EURUSD")
    pos_filter = build_broker_position_filter("EURUSD")
    print(_format_result(order_filter))
    print(
        f"Data -> order_filter_symbol='{get_broker_value_field(order_filter, 'symbol')}', position_filter_symbol='{get_broker_value_field(pos_filter, 'symbol')}'"
    )


def main() -> None:
    """Run canonical-contract examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-BRK-00 — contracts/ — Canonical Provider-Neutral Boundary\n\n"
        "Purpose: Define the versioned result, error, DTO, enum, page, event, and focused async capability contracts shared by every adapter.\n\n"
        "Module flow:\n"
        "-> caller/provider value\n"
        "-> enums.py canonical interpretation\n"
        "-> models.py immutable structural DTO\n"
        "-> protocols.py typed operation boundary\n"
        "-> StandardResponse"
    )

    # Stage 1: Enums & canonical interpretation
    fr_brokers_001_to_005_enums_and_interpretation()

    # Stage 2: Models & structural DTOs
    fr_brokers_006_to_038_models_and_dtos()

    # Stage 3: Typed operation boundary & mutation request envelopes
    fr_brokers_033_to_038_mutation_requests()


if __name__ == "__main__":
    main()
