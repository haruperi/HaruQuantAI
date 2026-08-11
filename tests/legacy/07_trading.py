# ruff: noqa: E501, BLE001, E402, N999
"""Unified usage example for generic Trading operations working with MT5 and cTrader."""

from __future__ import annotations

import asyncio
import os
import sys
import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal

# Add project root to sys.path to allow execution without PYTHONPATH issues
_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app.services.api import resolve_system_credential_slot
from app.services.brokers import (
    build_broker_margin_request,
    build_broker_order_modification_request,
    build_broker_order_request,
    build_broker_position_close_request,
    build_broker_position_modification_request,
    build_broker_profit_request,
    calculate_broker_margin,
    calculate_broker_profit,
    cancel_broker_order,
    close_broker_position,
    connect_broker,
    create_broker_adapter,
    disconnect_broker,
    get_broker_account_info,
    get_broker_id,
    get_broker_orders,
    get_broker_platform_info,
    get_broker_positions,
    get_broker_quote,
    get_broker_symbol_info,
    get_broker_value_field,
    list_broker_deal_history,
    list_broker_order_history,
    modify_broker_order,
    modify_broker_position,
    place_broker_order,
    resolve_provider_connection_config,
)
from app.services.risk import (
    create_action_policy_verdict,
    create_risk_approval_token,
    create_risk_decision_package,
    get_decision_state,
)
from app.services.trading import (
    create_live_session,
    start_live_session,
    stop_live_session,
)
from app.utils import generate_id, load_broker_provider_settings

Target = Literal["sim", "mt5", "ctrader"]
EXECUTION_TARGET: Target = "mt5"


@dataclass
class OperationsContext:
    """Private usage-only state shared across trading examples."""

    target: Target
    adapter: object | None
    connection: object | None
    store: Any
    connected: bool
    account_id: str
    symbol: str
    position_id: str
    order_id: str
    live_session: object | None = None
    placed_order_id: str | None = None


# Shared context instance
ctx = OperationsContext(
    target=EXECUTION_TARGET,
    adapter=None,
    connection=None,
    store=None,
    connected=False,
    account_id="acc-001",
    symbol="GBPUSD",
    position_id="pos-001",
    order_id="ord-001",
)


def _status(result: object) -> str:
    """Return canonical status string from response object."""
    return str(get_broker_value_field(result, "status"))


def _bounded_data(result: object) -> object:
    """Return bounded data payload from response object."""
    data = get_broker_value_field(result, "data")
    return "<none>" if data is None else repr(data)[:500]


def _meta(value: object) -> Mapping[str, object] | None:
    """Extract metadata mapping from standard object or response dict.

    Args:
        value: Source DTO or mapping.

    Returns:
        Extracted metadata dictionary or None.
    """
    if isinstance(value, Mapping):
        return (
            value.get("endpoint_metadata")
            or value.get("provider_metadata")
            or value.get("details")
        )  # type: ignore[return-value]
    for key in ("endpoint_metadata", "provider_metadata", "details"):
        try:
            m = get_broker_value_field(value, key)
            if isinstance(m, Mapping):
                return m
        except AttributeError, TypeError, ValueError:
            m = getattr(value, key, None)
            if isinstance(m, Mapping):
                return m
    return None


def _value(value: object, field: str, default: object = "N/A") -> object:
    """Extract one field from DTO or mapping safely.

    Args:
        value: Source DTO or mapping.
        field: Field name to extract.
        default: Fallback value.

    Returns:
        Extracted field value or default fallback.
    """
    if value is None:
        return default
    if isinstance(value, Mapping) and field in value:
        return value[field]
    try:
        res = get_broker_value_field(value, field)
        if res is not None:
            return res
    except AttributeError, TypeError, ValueError:
        res = getattr(value, field, None)
        if res is not None:
            return res
    meta = _meta(value)
    if meta is not None and field in meta:
        return meta[field]
    return default


def _response_data(label: str, result: object) -> object | None:
    """Return successful response data or display failure evidence."""
    status = _status(result)
    data = get_broker_value_field(result, "data")
    if status == "success" and data is not None:
        return data
    error = get_broker_value_field(result, "error")
    print(f"{label}: FAILED")
    print(f"Status:            {status}")
    print(f"Error:             {_value(error, 'code', 'Unavailable')}")
    print(f"Message:           {_value(error, 'message', 'No provider data returned')}")
    return None


def _print_section(title: str, fields: tuple[tuple[str, object], ...]) -> None:
    """Print one formatted section with label/value pairs."""
    print(f"\n{title}")
    print("-" * 60)
    for label, val in fields:
        print(f"{label + ':':<20}{val}")


def _display_fields(
    value: object,
    fields: tuple[tuple[str, str], ...],
    *,
    virtual: bool,
) -> tuple[tuple[str, object], ...]:
    """Build ordered canonical display fields with virtual provenance.

    Args:
        value: Source object.
        fields: Label and field-name pairs.
        virtual: Virtual flag.

    Returns:
        Ordered label and extracted value tuples.
    """
    rendered = [(label, _value(value, field)) for label, field in fields]
    rendered.append(("Virtual", "Yes" if virtual else "No"))
    return tuple(rendered)


def _render_platform(value: object, *, virtual: bool = False) -> None:
    """Render platform evidence."""
    connected_val = _value(value, "connected", default=None)
    trade_allowed_val = _value(value, "trade_allowed", default=None)
    dlls_allowed_val = _value(value, "dlls_allowed", default=None)

    connected_str = (
        "Yes"
        if connected_val is True
        else ("No" if connected_val is False else ("Yes" if virtual else "N/A"))
    )
    trade_allowed_str = (
        "Yes"
        if trade_allowed_val is True
        else ("No" if trade_allowed_val is False else "N/A")
    )
    dlls_allowed_str = (
        "Yes"
        if dlls_allowed_val is True
        else ("No" if dlls_allowed_val is False else "N/A")
    )

    _print_section(
        "PLATFORM INFORMATION",
        (
            ("Broker", _value(value, "broker_id")),
            ("Provider", _value(value, "provider_name")),
            ("Product Profile", _value(value, "product_profile")),
            ("Environment", _value(value, "environment")),
            ("API/Terminal", _value(value, "api_or_terminal_version")),
            ("Observed At", _value(value, "observed_at")),
            ("Name", _value(value, "name", default=_value(value, "provider_name"))),
            ("Company", _value(value, "company")),
            (
                "Build",
                _value(
                    value, "build", default=_value(value, "api_or_terminal_version")
                ),
            ),
            ("Language", _value(value, "language")),
            ("Connected", connected_str),
            ("Trade Allowed", trade_allowed_str),
            ("DLLs Allowed", dlls_allowed_str),
            ("Ping Last (us)", _value(value, "ping_last")),
            ("Path", _value(value, "path")),
            ("Data Path", _value(value, "data_path")),
            ("Common Data Path", _value(value, "common_data_path")),
            ("Virtual", "Yes" if virtual else "No"),
        ),
    )


def _render_account(value: object, *, virtual: bool = False) -> None:
    """Render canonical account evidence."""
    currency = _value(value, "currency")
    margin_raw = _value(value, "margin", None)
    equity_raw = _value(value, "equity", None)
    margin_level_val = _value(value, "margin_level", None)

    margin_level_str = "N/A (no open positions)"
    if margin_level_val not in (None, "N/A"):
        margin_level_str = f"{float(margin_level_val):.2f}%"  # type: ignore[arg-type]
    elif margin_raw not in (None, 0, "N/A") and equity_raw not in (None, "N/A"):
        try:
            m_val = float(margin_raw)  # type: ignore[arg-type]
            e_val = float(equity_raw)  # type: ignore[arg-type]
            if m_val > 0:
                margin_level_str = f"{(e_val / m_val) * 100:.2f}%"
        except ValueError, TypeError:
            pass

    trade_mode = _value(value, "trade_mode", default="DEMO")
    trade_mode_desc = _value(value, "trade_mode_description", default="Demo account")
    margin_mode = _value(value, "margin_mode", default="HEDGING")
    margin_mode_desc = _value(
        value, "margin_mode_description", default="Hedging position accounting"
    )

    trade_allowed_raw = _value(value, "trade_allowed", default=True)
    trade_expert_raw = _value(value, "trade_expert", default=True)
    limit_orders = _value(value, "limit_orders", default=0)

    trade_allowed_str = (
        "Yes"
        if trade_allowed_raw is True
        else ("No" if trade_allowed_raw is False else "N/A")
    )
    trade_expert_str = (
        "Yes"
        if trade_expert_raw is True
        else ("No" if trade_expert_raw is False else "N/A")
    )

    leverage_val = _value(value, "leverage", default=100)
    leverage_str = f"1:{leverage_val}" if leverage_val != "N/A" else "N/A"
    limit_orders_str = f"{limit_orders} (0 = unlimited)"

    _print_section(
        "ACCOUNT IDENTITY",
        (
            ("Login", _value(value, "login", default=_value(value, "account_id"))),
            (
                "Name",
                _value(
                    value, "name", default=_value(value, "account_reference_redacted")
                ),
            ),
            ("Server", _value(value, "server")),
            ("Company", _value(value, "company")),
            ("Currency", currency),
            ("Leverage", leverage_str),
            ("Account Reference", _value(value, "account_reference_redacted")),
            ("Status", _value(value, "status")),
            ("Retrieved At", _value(value, "retrieved_at")),
            ("Provider Time", _value(value, "provider_timestamp")),
            ("Virtual", "Yes" if virtual else "No"),
        ),
    )
    _print_section(
        "ACCOUNT MODE",
        (
            ("Trade Mode", f"{trade_mode} ({trade_mode_desc})"),
            ("Margin Mode", f"{margin_mode} ({margin_mode_desc})"),
        ),
    )
    _print_section(
        "PERMISSIONS",
        (
            ("Trade Allowed", trade_allowed_str),
            ("Expert Allowed", trade_expert_str),
            ("Limit Orders", limit_orders_str),
        ),
    )
    _print_section(
        "BALANCE & EQUITY",
        (
            ("Balance", f"{_value(value, 'balance')} {currency}"),
            ("Credit", f"{_value(value, 'credit', default='0.00')} {currency}"),
            ("Profit", f"{_value(value, 'profit', default='0.00')} {currency}"),
            ("Equity", f"{_value(value, 'equity')} {currency}"),
        ),
    )
    _print_section(
        "MARGIN INFORMATION",
        (
            ("Margin Used", f"{_value(value, 'margin')} {currency}"),
            ("Free Margin", f"{_value(value, 'free_margin')} {currency}"),
            ("Margin Level", margin_level_str),
            ("Margin Stopout", _value(value, "margin_so_level", default="0.0")),
        ),
    )


def _render_symbol(value: object, *, virtual: bool = False) -> None:
    """Render symbol specifications."""
    symbol_name = _value(value, "name", default=_value(value, "provider_symbol"))
    digits_val = int(
        _value(value, "digits", default=_value(value, "price_precision", default=5))
    )
    point_val = _value(
        value, "point", default=_value(value, "price_step", default=0.00001)
    )
    tick_size_val = _value(
        value, "tick_size", default=_value(value, "price_step", default=0.00001)
    )

    bid_val = _value(value, "bid", default=_value(value, "bid_price", default=None))
    ask_val = _value(value, "ask", default=_value(value, "ask_price", default=None))
    last_val = _value(value, "last", default=_value(value, "last_price", default=None))
    spread_val = _value(value, "spread", default=None)

    def _fmt_price(val: object) -> str:
        if val in (None, "N/A"):
            return "N/A"
        try:
            return f"{float(val):.{digits_val}f}"  # type: ignore[arg-type]
        except ValueError, TypeError:
            return str(val)

    bid_str = _fmt_price(bid_val)
    ask_str = _fmt_price(ask_val)
    last_str = _fmt_price(last_val)
    spread_str = f"{spread_val} points" if spread_val not in (None, "N/A") else "N/A"

    trade_mode = _value(value, "trade_mode", default="FULL")
    trade_mode_desc = _value(
        value, "trade_mode_description", default="Full trading access"
    )

    contract_size_val = _value(value, "contract_size", default=100000.0)
    contract_size_str = (
        f"{float(contract_size_val):.2f}" if contract_size_val != "N/A" else "N/A"
    )

    min_lot_val = _value(
        value, "volume_min", default=_value(value, "min_quantity", default=0.01)
    )
    min_lot_str = f"{float(min_lot_val):.2f}" if min_lot_val != "N/A" else "N/A"

    max_lot_val = _value(
        value, "volume_max", default=_value(value, "max_quantity", default=100.0)
    )
    max_lot_str = f"{float(max_lot_val):.2f}" if max_lot_val != "N/A" else "N/A"

    lot_step_val = _value(
        value, "volume_step", default=_value(value, "quantity_step", default=0.01)
    )
    lot_step_str = f"{float(lot_step_val):.2f}" if lot_step_val != "N/A" else "N/A"

    swap_mode_str = _value(value, "swap_mode", default="POINTS")
    swap_long_val = _value(value, "swap_long", default=0.0)
    swap_long_str = f"{float(swap_long_val):.2f}" if swap_long_val != "N/A" else "N/A"

    swap_short_val = _value(value, "swap_short", default=0.0)
    swap_short_str = (
        f"{float(swap_short_val):.2f}" if swap_short_val != "N/A" else "N/A"
    )

    _print_section(
        "SYMBOL SPECIFICATIONS",
        (
            ("Symbol", symbol_name),
            ("Digits", digits_val),
            ("Point", point_val),
            ("Tick Size", tick_size_val),
            ("Product Profile", _value(value, "product_profile")),
            ("Base Asset", _value(value, "base_asset")),
            ("Quote Asset", _value(value, "quote_asset")),
            ("Virtual", "Yes" if virtual else "No"),
        ),
    )
    _print_section(
        "CURRENT PRICES",
        (
            ("Bid", bid_str),
            ("Ask", ask_str),
            ("Last", last_str),
            ("Spread", spread_str),
        ),
    )
    _print_section(
        "TRADING INFORMATION",
        (("Trade Mode", f"{trade_mode} ({trade_mode_desc})"),),
    )
    _print_section(
        "LOT PARAMETERS",
        (
            ("Contract Size", contract_size_str),
            ("Min Lot", min_lot_str),
            ("Max Lot", max_lot_str),
            ("Lot Step", lot_step_str),
        ),
    )
    _print_section(
        "SWAP INFORMATION",
        (
            ("Swap Mode", swap_mode_str),
            ("Swap Long", swap_long_str),
            ("Swap Short", swap_short_str),
        ),
    )


def _page_items(value: object) -> tuple[object, ...]:
    """Return at most five canonical page items."""
    items = _value(value, "items", ())
    return tuple(items or ())[:5]  # type: ignore[arg-type]


def _render_positions(value: object, *, virtual: bool = False) -> None:
    """Render position page."""
    items = _page_items(value)
    print(f"Positions found: {len(items)}")
    for index, item in enumerate(items, start=1):
        _print_section(
            f"POSITION {index}",
            _display_fields(
                item,
                (
                    ("Position ID", "position_id"),
                    ("Symbol", "symbol"),
                    ("Side", "side"),
                    ("State", "state"),
                    ("Quantity", "quantity"),
                    ("Quantity Unit", "quantity_unit"),
                    ("Open Price", "open_price"),
                    ("Current Price", "current_price"),
                    ("Profit", "profit"),
                    ("Swap", "swap"),
                    ("Currency", "currency"),
                    ("Stop Loss", "stop_loss"),
                    ("Take Profit", "take_profit"),
                    ("Provider Time", "provider_timestamp"),
                    ("Retrieved At", "retrieved_at"),
                ),
                virtual=virtual,
            ),
        )


def _render_orders(value: object, *, title: str, virtual: bool = False) -> None:
    """Render order page."""
    items = _page_items(value)
    print(f"{title} found: {len(items)}")
    for index, item in enumerate(items, start=1):
        _print_section(
            f"{title.upper()} {index}",
            _display_fields(
                item,
                (
                    ("Order ID", "order_id"),
                    ("Client Order ID", "client_order_id"),
                    ("Symbol", "symbol"),
                    ("Side", "side"),
                    ("Order Type", "order_type"),
                    ("State", "state"),
                    ("Quantity", "quantity"),
                    ("Filled", "filled"),
                    ("Remaining", "remaining"),
                    ("Quantity Unit", "quantity_unit"),
                    ("Price", "price"),
                    ("Stop Price", "stop_price"),
                    ("Time In Force", "time_in_force"),
                    ("Product Profile", "product_profile"),
                    ("Provider Time", "provider_timestamp"),
                    ("Retrieved At", "retrieved_at"),
                ),
                virtual=virtual,
            ),
        )


def _render_deals(value: object, *, virtual: bool = False) -> None:
    """Render deal page."""
    items = _page_items(value)
    print(f"Historical deals found: {len(items)}")
    for index, item in enumerate(items, start=1):
        _print_section(
            f"DEAL {index}",
            _display_fields(
                item,
                (
                    ("Deal ID", "deal_id"),
                    ("Order ID", "order_id"),
                    ("Position ID", "position_id"),
                    ("Symbol", "symbol"),
                    ("Side", "side"),
                    ("Quantity", "quantity"),
                    ("Quantity Unit", "quantity_unit"),
                    ("Price", "price"),
                    ("Partial", "partial"),
                    ("Fee", "fee"),
                    ("Fee Currency", "fee_currency"),
                    ("Provider Time", "provider_timestamp"),
                    ("Retrieved At", "retrieved_at"),
                ),
                virtual=virtual,
            ),
        )


def _render_execution(label: str, result: object) -> None:
    """Render execution receipt or broker order result."""
    value = _response_data(label, result)
    if value is None:
        return

    if hasattr(value, "outcome") or (isinstance(value, dict) and "outcome" in value):
        order_id = _value(value, "order_id")
        deal_ids = _value(value, "deal_ids")
        outcome = _value(value, "outcome")
        filled = _value(value, "filled_quantity")
        remaining = _value(value, "remaining_quantity")
        avg_price = _value(value, "average_price")
        p_code = _value(value, "provider_code")
        p_msg = _value(value, "provider_message")
        retrieved_at = _value(value, "retrieved_at")

        if deal_ids != "N/A" and isinstance(deal_ids, (list, tuple)):
            deal_ids_str = ", ".join(str(d) for d in deal_ids)
        else:
            deal_ids_str = str(deal_ids)

        _print_section(
            label.upper(),
            (
                ("Outcome", outcome),
                ("Order ID (Ticket)", order_id),
                ("Deal IDs (Tickets)", deal_ids_str),
                ("Filled Quantity", filled),
                ("Remaining Quantity", remaining),
                ("Average Price", avg_price),
                ("Provider Code", p_code),
                ("Provider Message", p_msg),
                ("Retrieved At", retrieved_at),
            ),
        )
        return

    if hasattr(value, "position_id") and hasattr(value, "stop_loss"):
        _print_section(
            label.upper(),
            (
                ("Status", "success"),
                ("Position ID (Ticket)", _value(value, "position_id")),
                ("Symbol", _value(value, "symbol")),
                ("Side", _value(value, "side")),
                ("Open Price", _value(value, "open_price")),
                ("Updated Stop Loss", _value(value, "stop_loss")),
                ("Updated Take Profit", _value(value, "take_profit")),
            ),
        )
        return

    _print_section(
        label.upper(),
        tuple(
            (field_label, _value(value, field))
            for field_label, field in (
                ("Receipt ID", "receipt_id"),
                ("Intent ID", "intent_id"),
                ("Client Order ID", "client_order_id"),
                ("Route", "route"),
                ("Authority", "authority"),
                ("Provider Order ID", "provider_order_id"),
                ("Provider Deal IDs", "provider_deal_ids"),
                ("Outcome", "status"),
                ("Requested Quantity", "requested_quantity"),
                ("Filled Quantity", "filled_quantity"),
                ("Average Price", "average_price"),
                ("Authority Time", "authority_timestamp"),
                ("Received At", "received_at"),
            )
        ),
    )


def _virtual_order_page() -> dict[str, object]:
    """Build bounded virtual order evidence.

    Returns:
        Dictionary containing virtual order page items.
    """
    return {
        "items": (
            {
                "order_id": "order-001",
                "client_order_id": "virtual-client-order-001",
                "symbol": "EURUSD",
                "side": "BUY",
                "order_type": "LIMIT",
                "state": "PENDING",
                "quantity": Decimal("1.00"),
                "filled": Decimal("0.00"),
                "remaining": Decimal("1.00"),
                "quantity_unit": "lots",
                "price": Decimal("1.0900"),
                "time_in_force": "GTC",
                "product_profile": "simulation",
                "retrieved_at": datetime.now(UTC),
            },
        )
    }


def _provider_mutations_enabled() -> bool:
    """Return whether genuine demo/paper provider mutations are enabled.

    Returns:
        True if provider mutations are enabled.
    """
    return True


def _live_action_policy(request: object) -> object:
    """Build dynamic action-policy verdict.

    Args:
        request: Action request.

    Returns:
        Action policy verdict object.
    """
    now = datetime.now(UTC)
    req_id = str(get_broker_value_field(request, "request_id"))
    wf_id = str(get_broker_value_field(request, "workflow_id"))
    corr_id = str(get_broker_value_field(request, "correlation_id"))
    action = str(get_broker_value_field(request, "action"))
    account_id = str(get_broker_value_field(request, "account_id"))
    verdict_id = str(
        get_broker_value_field(request, "action_policy_verdict_id") or "policy-001"
    )
    decision_id = str(get_broker_value_field(request, "risk_decision_id") or "risk-001")
    return create_action_policy_verdict(
        verdict_id=verdict_id,
        action=action,
        scope={"account_id": account_id},
        policy_version="policy-v1",
        attestation_id="attestation-001",
        decision_id=decision_id,
        reservation_id="reservation-001",
        allowed=True,
        reasons=(),
        issued_at=now - timedelta(minutes=1),
        expires_at=now + timedelta(minutes=10),
        request_id=req_id,
        workflow_id=wf_id,
        correlation_id=corr_id,
    )


def _live_risk_decision(request: object) -> object:
    """Build dynamic Risk approval decision.

    Args:
        request: Action request.

    Returns:
        Risk decision package object.
    """
    now = datetime.now(UTC)
    req_id = str(get_broker_value_field(request, "request_id"))
    wf_id = str(get_broker_value_field(request, "workflow_id"))
    corr_id = str(get_broker_value_field(request, "correlation_id"))
    action = str(get_broker_value_field(request, "action"))
    account_id = str(get_broker_value_field(request, "account_id"))
    decision_id = str(get_broker_value_field(request, "risk_decision_id") or "risk-001")
    intent_id = str(get_broker_value_field(request, "intent_id") or "intent-001")
    token_ref = str(
        get_broker_value_field(request, "approval_token_ref") or "token-001"
    )
    qty = get_broker_value_field(request, "quantity") or Decimal("1.00")

    token = create_risk_approval_token(
        token_id=token_ref,
        decision_id=decision_id,
        config_hash="a" * 64,
        action=action,
        scope={"account_id": account_id},
        approver_id="approver-001",
        issued_at=now - timedelta(minutes=1),
        expires_at=now + timedelta(minutes=10),
        nonce="nonce-001",
        signature="signature-001",
        request_id=req_id,
        workflow_id=wf_id,
        correlation_id=corr_id,
    )
    return create_risk_decision_package(
        decision_id=decision_id,
        intent_id=intent_id,
        state=get_decision_state("APPROVE"),
        requested_size=qty,
        approved_size=qty,
        ordered_checks=(),
        primary_failure_limit=None,
        composite_breach_flags=(),
        evidence_refs={"request": req_id},
        config_hash="a" * 64,
        concurrency_disclosure="serialized",
        recommendations=(),
        issued_at=now - timedelta(minutes=1),
        expires_at=now + timedelta(minutes=10),
        token=token,
        request_id=req_id,
        workflow_id=wf_id,
        correlation_id=corr_id,
    )


def _live_readiness(request: object, evidence: object) -> object:
    """Build dynamic readiness evidence.

    Args:
        request: Action request.
        evidence: Evidence input.

    Returns:
        Readiness assessment object.
    """
    del request, evidence
    return SimpleNamespace(passed=True, failed_check_codes=())


def _live_adapter_capability(request: object) -> dict[str, object]:
    """Build adapter capability evidence.

    Args:
        request: Action request.

    Returns:
        Adapter capability dictionary.
    """
    provider_id = str(get_broker_value_field(request, "provider_id") or "mt5")
    return {
        "provider_id": provider_id,
        "contract_version": "v1",
        "schema_id": "brokers.adapter.v1",
        "provider_api_version": "v1",
        "supported_actions": [
            "submit_order",
            "modify_order",
            "cancel_order",
            "modify_position",
            "close_position",
        ],
        "supported_order_types": ["MARKET", "LIMIT", "STOP"],
        "quantity_unit": "lots",
        "security_profile": "approved",
    }


def _provider_settings(target: str) -> object:
    """Load active provider settings with database credentials and environment overrides.

    Args:
        target: Provider identifier string (e.g. 'mt5' or 'ctrader').

    Returns:
        Loaded broker provider settings object.
    """
    explicit: dict[str, object] = {}
    if target == "mt5" or os.environ.get("MT5_ENABLED", "").lower() in (
        "true",
        "1",
        "yes",
    ):
        explicit["mt5_enabled"] = True
        explicit["mt5_environment"] = os.environ.get("MT5_ENVIRONMENT", "demo")

        try:
            slot = resolve_system_credential_slot("mt5", request_id=generate_id("req"))
            if isinstance(slot, dict):
                explicit["mt5_login"] = slot.get("login")
                explicit["mt5_password"] = slot.get("password")
                explicit["mt5_server"] = slot.get("server")
        except Exception as error:
            del error  # DB slot fallback is optional

        for env_key, setting_key in (
            ("MT5_LOGIN", "mt5_login"),
            ("MT5_PASSWORD", "mt5_password"),
            ("MT5_SERVER", "mt5_server"),
            ("MT5_TERMINAL_PATH", "mt5_terminal_path"),
        ):
            if env_key in os.environ:
                explicit[setting_key] = os.environ[env_key]

        explicit.setdefault(
            "mt5_terminal_path",
            r"C:\Program Files\Pepperstone MetaTrader 5\terminal64.exe",
        )
    elif target == "ctrader" or os.environ.get("CTRADER_ENABLED", "").lower() in (
        "true",
        "1",
        "yes",
    ):
        explicit["ctrader_enabled"] = True
        explicit["ctrader_environment"] = os.environ.get("CTRADER_ENVIRONMENT", "demo")
        for env_key, setting_key in (
            ("CTRADER_ACCOUNT_ID", "ctrader_account_id"),
            ("CTRADER_CLIENT_ID", "ctrader_client_id"),
            ("CTRADER_CLIENT_SECRET", "ctrader_client_secret"),
            ("CTRADER_ACCESS_TOKEN", "ctrader_access_token"),
        ):
            if env_key in os.environ:
                explicit[setting_key] = os.environ[env_key]
    return load_broker_provider_settings(explicit or None)


def example_01_connect() -> None:
    """Demonstrate connection to the active broker and live session initialization."""
    print("\n" + "=" * 100)
    print(f"--- 1. Connecting to Active Broker: {ctx.target.upper()} ---")
    print("=" * 100)

    try:
        b_config = resolve_provider_connection_config(
            get_broker_id(ctx.target),
            settings=_provider_settings(ctx.target),
        )

        if b_config is not None:
            created = create_broker_adapter(get_broker_id(ctx.target), b_config)
            if _status(created) == "success":
                adapter = get_broker_value_field(created, "data")
                if adapter is not None:
                    conn_res = asyncio.run(connect_broker(adapter))
                    status_val = _status(conn_res)

                    ctx.adapter = adapter
                    ctx.connection = b_config
                    ctx.connected = status_val == "success"

                    async def _passed() -> bool:
                        return True

                    flags = SimpleNamespace(
                        broker_id=ctx.target, environment=b_config.environment
                    )
                    session = create_live_session(
                        store=SimpleNamespace(projection=None, projections={}),
                        connection=b_config,
                        broker_adapter=adapter,
                        feature_flags=flags,
                        risk_decision_source=_live_risk_decision,
                        action_policy_source=_live_action_policy,
                        kill_switch_source=lambda _s: SimpleNamespace(disengaged=True),
                        readiness_source=_live_readiness,
                        adapter_capability_source=_live_adapter_capability,
                        auth_context_source=lambda _r: SimpleNamespace(authorized=True),
                        pre_audit_sink=lambda _ev: None,
                        event_sink=lambda _evt: None,
                        startup_reconcile=_passed,
                        drain_in_flight=_passed,
                        flush_evidence=_passed,
                        shutdown_reconcile=_passed,
                        clock=lambda: datetime.now(UTC),
                    )
                    ctx.live_session = session

                    config = {
                        "RUNTIME_PROFILE": "paper",
                        "EXECUTION_ROUTE": "paper",
                        "ALLOW_LIVE_MUTATIONS": True,
                        "LIVE_WORKFLOW_TIMEOUT_SECONDS": "30",
                        "SHUTDOWN_BUDGET_SECONDS": "5",
                        "IDEMPOTENCY_RETENTION_SECONDS": 600,
                        "CONCURRENCY_LOCK_TIMEOUT_SECONDS": "30",
                        "MAX_STALENESS_SECONDS": {
                            "route_snapshot": "30",
                            "risk_decision": "30",
                            "kill_switch": "30",
                        },
                        "DATA_AUTHORITY_ID": "data-authority-001",
                    }
                    evidence = {
                        "data_authority_id": "data-authority-001",
                        "adapter_security_profile": "approved",
                        "startup_evidence_fresh": True,
                    }
                    start_res = asyncio.run(
                        start_live_session(session, config, evidence)
                    )
                    _print_section(
                        "CONNECTION",
                        (
                            ("Target", ctx.target),
                            (
                                "Status",
                                "CONNECTED" if ctx.connected else "DISCONNECTED",
                            ),
                            ("Response Status", status_val),
                            ("Live Session Status", _value(start_res, "status")),
                            ("Virtual", "No"),
                        ),
                    )
                    return
    except Exception as e:
        print(f"Connection attempt raised exception: {e}")

    ctx.connected = False
    _print_section(
        "CONNECTION",
        (
            ("Target", ctx.target),
            ("Status", "FAILED / DISCONNECTED"),
            ("Virtual", "Yes"),
        ),
    )


def example_02_terminal() -> None:
    """Demonstrate fetching terminal / platform information."""
    print("\n" + "=" * 100)
    print("--- 2. Fetching Terminal Info ---")
    print("=" * 100)

    if ctx.adapter is not None:
        res = asyncio.run(get_broker_platform_info(ctx.adapter))
        val = _response_data("Terminal Info", res)
        if val is not None:
            _render_platform(val, virtual=False)
            return

    _render_platform(
        {
            "broker_id": ctx.target,
            "provider_name": "Virtual Provider",
            "product_profile": "simulation",
            "environment": "demo",
            "api_or_terminal_version": "v1.0.0",
            "observed_at": datetime.now(UTC),
            "name": "Virtual Terminal",
            "company": "HaruQuant Virtual",
            "build": "1000",
            "language": "English",
            "connected": True,
            "trade_allowed": True,
            "dlls_allowed": True,
            "ping_last": 1500,
            "path": "/virtual/terminal",
            "data_path": "/virtual/data",
            "common_data_path": "/virtual/common",
        },
        virtual=True,
    )


def example_03_account() -> None:
    """Demonstrate fetching canonical account information."""
    print("\n" + "=" * 100)
    print("--- 3. Fetching Account Information ---")
    print("=" * 100)

    if ctx.adapter is not None:
        res = asyncio.run(get_broker_account_info(ctx.adapter))
        val = _response_data("Account Info", res)
        if val is not None:
            _render_account(val, virtual=False)
            acc_id = _value(val, "account_id")
            if acc_id != "N/A":
                ctx.account_id = str(acc_id)
            return

    _render_account(
        {
            "account_id": "demo-acc-1001",
            "login": "10001",
            "name": "Demo Account",
            "server": "VirtualServer-Demo",
            "company": "HaruQuant Demo",
            "currency": "USD",
            "leverage": 100,
            "account_reference_redacted": "demo-***-1001",
            "status": "ACTIVE",
            "trade_mode": "DEMO",
            "margin_mode": "HEDGING",
            "trade_allowed": True,
            "trade_expert": True,
            "limit_orders": 0,
            "balance": "10000.00",
            "credit": "0.00",
            "profit": "0.00",
            "equity": "10000.00",
            "margin": "0.00",
            "free_margin": "10000.00",
            "margin_level": None,
            "retrieved_at": datetime.now(UTC),
        },
        virtual=True,
    )


def example_04_symbol() -> None:
    """Demonstrate fetching symbol specification and current price quote."""
    print("\n" + "=" * 100)
    print(f"--- 4. Fetching Symbol Information for {ctx.symbol} ---")
    print("=" * 100)

    if ctx.adapter is not None:
        sym_res = asyncio.run(get_broker_symbol_info(ctx.adapter, ctx.symbol))
        sym_val = _response_data("Symbol Info", sym_res)
        quote_res = asyncio.run(get_broker_quote(ctx.adapter, ctx.symbol))
        quote_val = _response_data("Quote Info", quote_res)

        if sym_val is not None:
            _render_symbol(sym_val, virtual=False)
        if quote_val is not None:
            _print_section(
                "CURRENT QUOTE",
                (
                    ("Symbol", _value(quote_val, "symbol")),
                    ("Bid", _value(quote_val, "bid")),
                    ("Ask", _value(quote_val, "ask")),
                    ("Last", _value(quote_val, "last_price")),
                    ("Retrieved At", _value(quote_val, "retrieved_at")),
                ),
            )
        if sym_val is not None:
            return

    _render_symbol(
        {
            "name": ctx.symbol,
            "digits": 5,
            "point": 0.00001,
            "tick_size": 0.00001,
            "product_profile": "spot_forex",
            "base_asset": "GBP",
            "quote_asset": "USD",
            "bid": 1.27500,
            "ask": 1.27520,
            "last": 1.27510,
            "spread": 20,
            "trade_mode": "FULL",
            "contract_size": 100000.0,
            "volume_min": 0.01,
            "volume_max": 100.0,
            "volume_step": 0.01,
            "swap_mode": "POINTS",
            "swap_long": -0.5,
            "swap_short": 0.1,
        },
        virtual=True,
    )


def example_05_position() -> None:
    """Demonstrate fetching current open positions."""
    print("\n" + "=" * 100)
    print("--- 5. Fetching Active Positions ---")
    print("=" * 100)

    if ctx.adapter is not None:
        res = asyncio.run(get_broker_positions(ctx.adapter))
        val = _response_data("Positions List", res)
        if val is not None:
            _render_positions(val, virtual=False)
            items = _page_items(val)
            if items:
                pos_id = _value(items[0], "position_id")
                if pos_id != "N/A":
                    ctx.position_id = str(pos_id)
            return

    _render_positions(
        {
            "items": (
                {
                    "position_id": "pos-001",
                    "symbol": ctx.symbol,
                    "side": "BUY",
                    "state": "OPEN",
                    "quantity": Decimal("0.02"),
                    "quantity_unit": "lots",
                    "open_price": Decimal("1.27500"),
                    "current_price": Decimal("1.27550"),
                    "profit": Decimal("10.00"),
                    "swap": Decimal("0.00"),
                    "currency": "USD",
                    "stop_loss": Decimal("1.26500"),
                    "take_profit": Decimal("1.28500"),
                    "retrieved_at": datetime.now(UTC),
                },
            )
        },
        virtual=True,
    )


def example_06_order() -> None:
    """Demonstrate fetching active pending orders."""
    print("\n" + "=" * 100)
    print("--- 6. Fetching Active Pending Orders ---")
    print("=" * 100)

    if ctx.adapter is not None:
        res = asyncio.run(get_broker_orders(ctx.adapter, limit=50))
        val = _response_data("Pending Orders List", res)
        if val is not None:
            _render_orders(val, title="Pending Order", virtual=False)
            items = _page_items(val)
            if items:
                ord_id = _value(items[0], "order_id")
                if ord_id != "N/A":
                    ctx.order_id = str(ord_id)
            return

    _render_orders(
        _virtual_order_page(),
        title="Pending Order",
        virtual=True,
    )


def example_07_history_order() -> None:
    """Demonstrate listing historical orders."""
    print("\n" + "=" * 100)
    print("--- 7. Fetching History Orders ---")
    print("=" * 100)

    end_dt = datetime.now(UTC)
    start_dt = end_dt - timedelta(days=30)

    if ctx.adapter is not None:
        res = asyncio.run(
            list_broker_order_history(
                ctx.adapter, start_time=start_dt, end_time=end_dt, limit=50
            )
        )
        val = _response_data("History Orders List", res)
        if val is not None:
            _render_orders(val, title="Historical Order", virtual=False)
            return

    _render_orders(
        {
            "items": (
                {
                    "order_id": "hist-ord-001",
                    "client_order_id": "client-hist-001",
                    "symbol": ctx.symbol,
                    "side": "BUY",
                    "order_type": "MARKET",
                    "state": "FILLED",
                    "quantity": Decimal("0.02"),
                    "filled": Decimal("0.02"),
                    "remaining": Decimal("0.00"),
                    "quantity_unit": "lots",
                    "price": Decimal("1.27500"),
                    "time_in_force": "IOC",
                    "product_profile": "spot_forex",
                    "retrieved_at": datetime.now(UTC),
                },
            )
        },
        title="Historical Order",
        virtual=True,
    )


def example_08_history_deal() -> None:
    """Demonstrate listing historical deals."""
    print("\n" + "=" * 100)
    print("--- 8. Fetching Historical Deals ---")
    print("=" * 100)

    end_dt = datetime.now(UTC)
    start_dt = end_dt - timedelta(days=30)

    if ctx.adapter is not None:
        res = asyncio.run(
            list_broker_deal_history(
                ctx.adapter, start_time=start_dt, end_time=end_dt, limit=50
            )
        )
        val = _response_data("History Deals List", res)
        if val is not None:
            _render_deals(val, virtual=False)
            return

    _render_deals(
        {
            "items": (
                {
                    "deal_id": "deal-001",
                    "order_id": "hist-ord-001",
                    "position_id": "pos-001",
                    "symbol": ctx.symbol,
                    "side": "BUY",
                    "quantity": Decimal("0.02"),
                    "quantity_unit": "lots",
                    "price": Decimal("1.27500"),
                    "partial": False,
                    "fee": Decimal("0.10"),
                    "fee_currency": "USD",
                    "retrieved_at": datetime.now(UTC),
                },
            )
        },
        virtual=True,
    )


def example_09_open_position() -> None:
    """Demonstrate submitting one governed market order."""
    print("\n" + "=" * 100)
    print(f"--- 9. Opening Position (Buy 0.02 {ctx.symbol}) ---")
    print("=" * 100)

    if ctx.adapter is not None and ctx.connected:
        o_req = build_broker_order_request(
            symbol=ctx.symbol,
            side="BUY",
            order_type="MARKET",
            quantity=Decimal("0.02"),
            quantity_unit="lots",
            environment=ctx.connection.environment if ctx.connection else "demo",
        )
        res = asyncio.run(place_broker_order(ctx.adapter, o_req))
        _render_execution("Submit Market Order", res)
        val = get_broker_value_field(res, "data")
        if val is not None:
            p_ord_id = _value(val, "order_id")
            if p_ord_id != "N/A":
                ctx.placed_order_id = str(p_ord_id)
        pos_res = asyncio.run(get_broker_positions(ctx.adapter))
        pos_val = get_broker_value_field(pos_res, "data")
        if pos_val is not None:
            items = _page_items(pos_val)
            for item in items:
                if _value(item, "symbol") == ctx.symbol:
                    pos_id = _value(item, "position_id")
                    if pos_id != "N/A":
                        ctx.position_id = str(pos_id)
                        break
            if not ctx.position_id and items:
                pos_id = _value(items[0], "position_id")
                if pos_id != "N/A":
                    ctx.position_id = str(pos_id)
        return

    _print_section(
        "SUBMIT MARKET ORDER (VIRTUAL / PACKAGED)",
        (
            ("Status", "success"),
            ("Action", "submit_order"),
            ("Symbol", ctx.symbol),
            ("Side", "BUY"),
            ("Quantity", "0.02 lots"),
            ("Order Type", "MARKET"),
            ("Mode", "Packaged / Simulation"),
            ("Virtual", "Yes"),
        ),
    )


def example_10_calc_profit_margin() -> None:
    """Demonstrate pre-trade profit and required margin calculation."""
    print("\n" + "=" * 100)
    print("--- 10. Pre-trade Profit and Margin Calculation ---")
    print("=" * 100)

    if ctx.adapter is not None:
        m_req = build_broker_margin_request(
            symbol=ctx.symbol,
            side="BUY",
            quantity=Decimal("0.02"),
            quantity_unit="lots",
            product_profile="mt5",
            price=Decimal("1.27500"),
        )
        m_res = asyncio.run(calculate_broker_margin(ctx.adapter, m_req))
        m_val = _value(m_res, "data")

        p_req = build_broker_profit_request(
            symbol=ctx.symbol,
            side="BUY",
            quantity=Decimal("0.02"),
            quantity_unit="lots",
            open_price=Decimal("1.27500"),
            close_price=Decimal("1.28500"),
            product_profile="mt5",
        )
        p_res = asyncio.run(calculate_broker_profit(ctx.adapter, p_req))
        p_val = _value(p_res, "data")

        _print_section(
            "CALCULATION RESULTS",
            (
                (
                    "Margin Required",
                    f"${m_val:.2f} USD" if isinstance(m_val, Decimal) else f"${m_val}",
                ),
                (
                    "Hypothetical Profit (+100 pips)",
                    f"${p_val:.2f} USD" if isinstance(p_val, Decimal) else f"${p_val}",
                ),
                ("Virtual", "No"),
            ),
        )
        return

    _print_section(
        "CALCULATION RESULTS",
        (
            ("Margin Required", "$25.50 USD"),
            ("Hypothetical Profit (+100 pips)", "$20.00 USD"),
            ("Virtual", "Yes"),
        ),
    )


def _calculate_dynamic_sltp(
    adapter: object, position: object, sl_pts: int = 100, tp_pts: int = 200
) -> tuple[Decimal, Decimal]:
    """Calculate dynamic Stop Loss and Take Profit prices from symbol points.

    Args:
        adapter: Active broker adapter instance.
        position: Target position item or object.
        sl_pts: Stop loss offset in points (default 100).
        tp_pts: Take profit offset in points (default 200).

    Returns:
        Tuple containing calculated (stop_loss, take_profit) Decimal values.
    """
    sym_name = str(_value(position, "symbol"))
    open_price = Decimal(str(_value(position, "open_price")))
    is_buy = str(_value(position, "side")).upper() in ("BUY", "LONG")

    sym_res = asyncio.run(get_broker_symbol_info(adapter, sym_name))
    sym_data = get_broker_value_field(sym_res, "data")

    precision = 5
    if sym_data is not None:
        prec = _value(sym_data, "price_precision")
        if prec != "N/A" and isinstance(prec, int):
            precision = prec

    point = Decimal(10) ** -precision
    if sym_data is not None:
        p_step = _value(sym_data, "price_step")
        if p_step != "N/A" and isinstance(p_step, Decimal):
            point = p_step
        else:
            meta = getattr(sym_data, "provider_metadata", {})
            if (
                isinstance(meta, (dict, Mapping))
                and "point" in meta
                and meta["point"] is not None
            ):
                point = Decimal(str(meta["point"]))

    sl_delta = Decimal(sl_pts) * point
    tp_delta = Decimal(tp_pts) * point
    sl = round(open_price - sl_delta if is_buy else open_price + sl_delta, precision)
    tp = round(open_price + tp_delta if is_buy else open_price - tp_delta, precision)
    return sl, tp


def example_11_modify_position() -> None:
    """Demonstrate modifying Stop Loss / Take Profit of an active position."""
    print("\n" + "=" * 100)
    print("--- 11. Modifying Active Position SL/TP ---")
    print("=" * 100)

    if ctx.adapter is not None and ctx.connected and ctx.position_id:
        sl_val: Decimal | None = None
        tp_val: Decimal | None = None

        pos_res = asyncio.run(get_broker_positions(ctx.adapter))
        pos_val = get_broker_value_field(pos_res, "data")
        if pos_val is not None:
            items = _page_items(pos_val)
            matching_pos = next(
                (
                    item
                    for item in items
                    if str(_value(item, "position_id")) == ctx.position_id
                ),
                None,
            )
            if matching_pos is None and items:
                matching_pos = next(
                    (item for item in items if _value(item, "symbol") == ctx.symbol),
                    None,
                )
                if matching_pos is not None:
                    ctx.position_id = str(_value(matching_pos, "position_id"))

            if matching_pos is not None:
                sl_val, tp_val = _calculate_dynamic_sltp(ctx.adapter, matching_pos)

        m_req = build_broker_position_modification_request(
            position_id=ctx.position_id,
            stop_loss=sl_val,
            take_profit=tp_val,
        )
        res = asyncio.run(modify_broker_position(ctx.adapter, m_req))
        _render_execution("Modify Position", res)
        return

    _print_section(
        "MODIFY POSITION (VIRTUAL / PACKAGED)",
        (
            ("Status", "success"),
            ("Position ID", ctx.position_id),
            ("New Stop Loss", "1.26500"),
            ("New Take Profit", "1.28500"),
            ("Virtual", "Yes"),
        ),
    )


def example_12_close_partial_position() -> None:
    """Demonstrate partial close of an active position (0.01 lot)."""
    print("\n" + "=" * 100)
    print("--- 12. Partial Closing Active Position (0.01 lot) ---")
    print("=" * 100)

    if ctx.adapter is not None and ctx.connected and ctx.position_id:
        c_req = build_broker_position_close_request(
            position_id=ctx.position_id,
            quantity=Decimal("0.01"),
            quantity_unit="lots",
        )
        res = asyncio.run(close_broker_position(ctx.adapter, c_req))
        _render_execution("Partial Close Position", res)
        return

    _print_section(
        "PARTIAL CLOSE POSITION (VIRTUAL / PACKAGED)",
        (
            ("Status", "success"),
            ("Position ID", ctx.position_id),
            ("Closed Quantity", "0.01 lots"),
            ("Remaining Quantity", "0.01 lots"),
            ("Virtual", "Yes"),
        ),
    )


def example_13_close_position() -> None:
    """Demonstrate closing the remaining active position fully."""
    print("\n" + "=" * 100)
    print("--- 13. Closing Remaining Position Fully ---")
    print("=" * 100)

    if ctx.adapter is not None and ctx.connected and ctx.position_id:
        c_req = build_broker_position_close_request(
            position_id=ctx.position_id,
            quantity=Decimal("0.01"),
            quantity_unit="lots",
        )
        res = asyncio.run(close_broker_position(ctx.adapter, c_req))
        _render_execution("Full Close Position", res)
        return

    _print_section(
        "FULL CLOSE POSITION (VIRTUAL / PACKAGED)",
        (
            ("Status", "success"),
            ("Position ID", ctx.position_id),
            ("Closed Quantity", "0.01 lots"),
            ("Remaining Quantity", "0.00 lots"),
            ("Virtual", "Yes"),
        ),
    )


def example_14_pending_orders() -> None:
    """Demonstrate placing a Buy Limit pending order."""
    print("\n" + "=" * 100)
    print("--- 14. Placing Pending Order (Buy Limit) ---")
    print("=" * 100)

    if ctx.adapter is not None and ctx.connected:
        o_req = build_broker_order_request(
            symbol=ctx.symbol,
            side="BUY",
            order_type="LIMIT",
            limit_price=Decimal("1.26500"),
            quantity=Decimal("0.01"),
            quantity_unit="lots",
            environment=ctx.connection.environment if ctx.connection else "demo",
        )
        res = asyncio.run(place_broker_order(ctx.adapter, o_req))
        _render_execution("Submit Buy Limit Order", res)
        val = get_broker_value_field(res, "data")
        if val is not None:
            p_ord_id = _value(val, "order_id")
            if p_ord_id != "N/A":
                ctx.order_id = str(p_ord_id)
        return

    _print_section(
        "SUBMIT PENDING BUY LIMIT (VIRTUAL / PACKAGED)",
        (
            ("Status", "success"),
            ("Action", "submit_order"),
            ("Order Type", "LIMIT"),
            ("Limit Price", "1.26500"),
            ("Quantity", "0.01 lots"),
            ("Virtual", "Yes"),
        ),
    )


def example_15_modify_pending_orders() -> None:
    """Demonstrate modifying a placed pending order."""
    print("\n" + "=" * 100)
    print("--- 15. Modifying Pending Order ---")
    print("=" * 100)

    if ctx.adapter is not None and ctx.connected and ctx.order_id:
        m_req = build_broker_order_modification_request(
            order_id=ctx.order_id,
            limit_price=Decimal("1.26400"),
            quantity=Decimal("0.01"),
        )
        res = asyncio.run(modify_broker_order(ctx.adapter, m_req))
        _render_execution("Modify Pending Order", res)
        return

    _print_section(
        "MODIFY PENDING ORDER (VIRTUAL / PACKAGED)",
        (
            ("Status", "success"),
            ("Order ID", ctx.order_id),
            ("New Limit Price", "1.26400"),
            ("Virtual", "Yes"),
        ),
    )


def example_16_delete_pending_orders() -> None:
    """Demonstrate deleting / cancelling a pending order."""
    print("\n" + "=" * 100)
    print("--- 16. Deleting/Cancelling Pending Order ---")
    print("=" * 100)

    if ctx.adapter is not None and ctx.connected and ctx.order_id:
        res = asyncio.run(cancel_broker_order(ctx.adapter, ctx.order_id))
        _render_execution("Cancel Pending Order", res)
        return

    _print_section(
        "CANCEL PENDING ORDER (VIRTUAL / PACKAGED)",
        (
            ("Status", "success"),
            ("Order ID", ctx.order_id),
            ("Outcome", "CANCELLED"),
            ("Virtual", "Yes"),
        ),
    )


def example_17_shutdown() -> None:
    """Demonstrate shutting down connection to active broker."""
    print("\n" + "=" * 100)
    print(f"--- 17. Shutting down connection to {ctx.target.upper()} ---")
    print("=" * 100)

    status_val = "success"
    if ctx.adapter is not None:
        disc_res = asyncio.run(disconnect_broker(ctx.adapter))
        status_val = _status(disc_res)

    if ctx.live_session is not None:
        asyncio.run(stop_live_session(ctx.live_session))

    _print_section(
        "SHUTDOWN",
        (
            ("Target", ctx.target),
            ("Status", status_val),
            ("Authority Released", "Yes"),
            ("Virtual", "No" if ctx.adapter is not None else "Yes"),
        ),
    )


if __name__ == "__main__":
    example_01_connect()
    example_02_terminal()
    example_03_account()
    example_04_symbol()
    example_05_position()
    example_06_order()
    example_07_history_order()
    example_08_history_deal()
    example_09_open_position()
    example_10_calc_profit_margin()
    time.sleep(2)
    example_11_modify_position()
    time.sleep(2)
    example_12_close_partial_position()
    time.sleep(2)
    example_13_close_position()
    time.sleep(2)
    example_14_pending_orders()
    time.sleep(2)
    example_15_modify_pending_orders()
    time.sleep(2)
    example_16_delete_pending_orders()
    example_17_shutdown()
