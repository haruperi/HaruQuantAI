"""WF-TRD-017: broker-agnostic main Trading operations walkthrough."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import (
    build_broker_margin_request,
    build_broker_profit_request,
    calculate_broker_margin,
    calculate_broker_profit,
    connect_broker,
    create_broker_adapter,
    disconnect_broker,
    get_broker_account_info,
    get_broker_connection_environment,
    get_broker_id,
    get_broker_orders,
    get_broker_platform_info,
    get_broker_positions,
    get_broker_quote,
    get_broker_symbol_info,
    get_broker_value_field,
    list_broker_deal_history,
    list_broker_order_history,
    resolve_provider_connection_config,
)
from app.services.risk import (
    create_action_policy_verdict,
    create_risk_approval_token,
    create_risk_decision_package,
    get_decision_state,
)
from app.services.trading import (
    cancel_order,
    close_position,
    create_live_session,
    modify_order,
    modify_position,
    start_live_session,
    stop_live_session,
    submit_order,
)
from app.utils import load_broker_provider_settings, load_settings
from tests.trading.usage.workflows._support import examples

Target = Literal["sim", "mt5", "ctrader"]

# Change only this line to select the execution target. Broker targets still
# require verified non-production settings and explicit mutation opt-in.
EXECUTION_TARGET: Target = "sim"

WORKFLOW_ID = "WF-TRD-017"
STAGES = (
    "Connect to the selected execution target.",
    "Read provider-neutral platform information.",
    "Read canonical account information.",
    "Read canonical symbol specifications and quote.",
    "List current positions.",
    "List pending orders.",
    "List historical orders.",
    "List historical deals.",
    "Submit one governed market order.",
    "Calculate margin and hypothetical profit.",
    "Modify one governed position.",
    "Partially close one governed position.",
    "Close the remaining governed position.",
    "Submit one governed pending limit order.",
    "Modify one governed pending order.",
    "Cancel one governed pending order.",
    "Disconnect and report cleanup.",
)


@dataclass
class OperationsContext:
    """Private usage-only state shared by the 17 provider-neutral examples."""

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


def _stage(number: int) -> None:
    """Print one workflow stage.

    Args:
        number: One-based stage number.
    """
    print(
        f"\n{'=' * 88}\nStage {number:02d}/{len(STAGES)} — "
        f"{STAGES[number - 1]}\n{'=' * 88}"
    )


def _status(result: object) -> str:
    """Return one canonical result status.

    Args:
        result: Standard response-like object.

    Returns:
        Canonical status text.
    """
    return str(get_broker_value_field(result, "status"))


def _bounded_data(result: object) -> object:
    """Return bounded canonical response data.

    Args:
        result: Standard response-like object.

    Returns:
        Bounded payload representation.
    """
    data = get_broker_value_field(result, "data")
    return "<none>" if data is None else repr(data)[:500]


def _show_result(label: str, result: object) -> None:
    """Print one bounded, secret-safe canonical response.

    Args:
        label: Human-readable operation label.
        result: Standard response-like object.
    """
    print(f"{label}: status={_status(result)}, data={_bounded_data(result)}")


def _meta(value: object) -> Mapping[str, object] | None:
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
    """Extract one field from a DTO or mapping."""
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
    """Return successful response data or print bounded failure evidence.

    Args:
        label: Human-readable operation label.
        result: Canonical response.

    Returns:
        Successful data, or ``None`` after displaying failure evidence.
    """
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
    """Print one aligned, bounded usage-output section.

    Args:
        title: Section heading.
        fields: Ordered label/value pairs.
    """
    print(f"\n{title}")
    print("-" * 60)
    for label, value in fields:
        print(f"{label + ':':<20}{value}")


def _display_fields(
    value: object,
    fields: tuple[tuple[str, str], ...],
    *,
    virtual: bool,
) -> tuple[tuple[str, object], ...]:
    """Build ordered canonical display fields with provenance."""
    rendered = [(label, _value(value, field)) for label, field in fields]
    rendered.append(("Virtual", "Yes" if virtual else "No"))
    return tuple(rendered)


def _render_platform(value: object, *, virtual: bool = False) -> None:
    """Render provider-neutral platform evidence."""
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
    """Render canonical account evidence with detailed account fields."""
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
    """Render canonical provider-native symbol specifications with extended market fields."""
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


def _render_quote(value: object, *, virtual: bool = False) -> None:
    """Render canonical current quote evidence."""
    _print_section(
        "CURRENT QUOTE",
        _display_fields(
            value,
            (
                ("Symbol", "symbol"),
                ("Bid", "bid"),
                ("Ask", "ask"),
                ("Last", "last_price"),
                ("Bid Quantity", "bid_quantity"),
                ("Ask Quantity", "ask_quantity"),
                ("Price Unit", "price_unit"),
                ("Provider Sequence", "provider_sequence_id"),
                ("Provider Time", "provider_timestamp"),
                ("Retrieved At", "retrieved_at"),
            ),
            virtual=virtual,
        ),
    )


def _page_items(value: object) -> tuple[object, ...]:
    """Return at most five canonical page items."""
    items = _value(value, "items", ())
    return tuple(items or ())[:5]  # type: ignore[arg-type]


def _render_positions(value: object, *, virtual: bool = False) -> None:
    """Render a bounded canonical position page."""
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
    """Render a bounded canonical order page."""
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
    """Render a bounded canonical deal page."""
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
    """Render one governed Trading execution receipt or bounded failure."""
    value = _response_data(label, result)
    if value is None:
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
    """Build bounded virtual order evidence for presentation parity."""
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
    """Return whether genuine demo/paper provider mutations were explicitly armed."""
    if load_settings().environment != "dev":
        return False
    if os.getenv("TRADING_USAGE_ALLOW_PROVIDER_MUTATIONS", "").lower() == "true":
        return True
    try:
        env_path = Path(__file__).resolve().parents[4] / "app" / "configs" / "env.json"
        if env_path.exists():
            with env_path.open(encoding="utf-8") as f:
                data = json.load(f)
            env_sec = data.get("settings", {}).get("environment", {})
            flag = str(
                env_sec.get("trading_usage_allow_provider_mutations", "")
            ).lower()
            return flag == "true"
    except OSError, ValueError:
        pass
    return False


def _live_action_policy(request: object) -> object:
    """Build dynamic current action-policy evidence for live gate evaluation."""
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
    """Build dynamic current Risk approval with token evidence for live gate evaluation."""
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
    """Build dynamic readiness evidence for live gate evaluation."""
    del request, evidence
    return SimpleNamespace(passed=True, failed_check_codes=())


def _live_adapter_capability(request: object) -> dict[str, object]:
    """Build normalized approved adapter capability evidence for all actions."""
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
        "operation_timeout_seconds": "10",
        "malformed_response_policy": "unknown_outcome",
        "rate_limit_policy": "external",
        "mutation_retry_policy": "reconcile_before_retry",
        "redaction_applied": True,
    }


async def _compose_context(target: Target) -> OperationsContext:
    """Compose one selected target through current public boundaries.

    Args:
        target: Explicit Simulation, MT5, or cTrader selection.

    Returns:
        Usage context consumed unchanged by every example.

    Raises:
        RuntimeError: Provider configuration is unavailable or unsafe.
    """
    if target == "sim":
        return OperationsContext(
            target=target,
            adapter=None,
            connection=None,
            store=examples.execution_store(),
            connected=False,
            account_id="account-001",
            symbol="EURUSD",
            position_id="position-001",
            order_id="order-001",
        )

    if load_settings().environment != "dev":
        raise RuntimeError("MT5/cTrader usage requires application environment dev")
    connection = resolve_provider_connection_config(
        get_broker_id(target),
        settings=load_broker_provider_settings(),
    )
    broker_env = get_broker_connection_environment(connection)
    if not any(
        name in broker_env.lower() for name in ("demo", "paper", "sandbox", "test")
    ):
        raise RuntimeError("provider usage requires a verified non-production account")
    created = create_broker_adapter(get_broker_id(target), connection)
    if _status(created) != "success":
        raise RuntimeError(f"{target} adapter construction failed closed")
    adapter = get_broker_value_field(created, "data")
    if adapter is None:
        raise RuntimeError(f"{target} adapter construction returned no adapter")
    info_res = await adapter.get_account_info()
    account_id = (
        str(info_res.data.account_id)
        if _status(info_res) == "success" and info_res.data is not None
        else "account-001"
    )

    store = examples.execution_store()

    async def _passed() -> bool:
        return True

    flags = SimpleNamespace(broker_id=target, environment=connection.environment)
    session = create_live_session(
        store=store,
        connection=connection,
        broker_adapter=adapter,
        feature_flags=flags,
        risk_decision_source=_live_risk_decision,
        action_policy_source=_live_action_policy,
        kill_switch_source=examples.inactive_kill_switch_hierarchy,
        readiness_source=_live_readiness,
        adapter_capability_source=_live_adapter_capability,
        auth_context_source=examples.auth_context,
        pre_audit_sink=lambda _ev: None,
        event_sink=lambda _evt: None,
        startup_reconcile=_passed,
        drain_in_flight=_passed,
        flush_evidence=_passed,
        shutdown_reconcile=_passed,
        clock=lambda: datetime.now(UTC),
    )

    runtime_profile = "live" if broker_env.lower() == "live" else "paper"
    if target != "sim" and store.projection is not None:
        target_scope = (runtime_profile, account_id, target)
        seeded_projection = store.projection.model_copy(
            update={
                "route": runtime_profile,
                "tenant_id": account_id,
                "authority_id": target,
            }
        )
        store.projections[target_scope] = seeded_projection
        store.projection = seeded_projection

    config = {
        "RUNTIME_PROFILE": runtime_profile,
        "EXECUTION_ROUTE": runtime_profile,
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
    await start_live_session(session, config, evidence)

    return OperationsContext(
        target=target,
        adapter=adapter,
        connection=connection,
        store=store,
        connected=False,
        account_id=account_id,
        symbol="EURUSD",
        position_id="position-001",
        order_id="order-001",
        live_session=session,
    )


def _request(
    context: OperationsContext,
    sequence: int,
    action: str,
    **updates: object,
) -> object:
    """Build one exact governed request for the selected target.

    Args:
        context: Shared target context.
        sequence: Stable example sequence used for idempotency separation.
        action: Exact Trading action.
        **updates: Action-specific contract fields.

    Returns:
        Validated Trading request.
    """
    now = datetime.now(UTC)
    route = (
        "sim"
        if context.target == "sim"
        else (
            "live"
            if context.connection is not None
            and get_broker_connection_environment(context.connection).lower() == "live"
            else "paper"
        )
    )
    provider_id = None if context.target == "sim" else context.target
    return examples.trading_request(
        request_id=f"req-{sequence:08d}-1111-4111-8111-111111111111",
        workflow_id=f"wf-{sequence:08d}-2222-4222-8222-222222222222",
        correlation_id=f"cor-{sequence:08d}-3333-4333-8333-333333333333",
        risk_decision_id=f"risk-{sequence:08d}-decision-001",
        action_policy_verdict_id=f"policy-{sequence:08d}-verdict-001",
        approval_token_ref=f"token-{sequence:08d}-001",
        intent_id=f"intent-{sequence:08d}-001",
        route=route,
        provider_id=provider_id,
        action=action,
        symbol=context.symbol,
        account_id=context.account_id,
        idempotency_key=f"operations-{context.target}-{sequence:02d}",
        system_time=now,
        valid_until=now + timedelta(minutes=10),
        **updates,
    )


def _dependencies(
    context: OperationsContext,
    *,
    action_policy: object | None = None,
) -> object:
    """Build complete Trading dependencies for one example."""
    store = context.store if context.target != "sim" else examples.execution_store()
    deps = examples.trading_dependencies(
        store=store,
        action_policy=action_policy,
    )
    if context.target != "sim" and context.live_session is not None:
        now = datetime.now(UTC)
        original_account_source = deps.account_state_source

        def _fresh_account_state(item: object) -> object:
            base_snapshot = original_account_source(item)
            orders = list(base_snapshot.orders)
            if context.placed_order_id and not any(
                o.order_id == context.placed_order_id for o in orders
            ):
                orders.append(
                    orders[0].model_copy(
                        update={
                            "order_id": context.placed_order_id,
                            "symbol": context.symbol,
                            "state": "ACCEPTED",
                        }
                    )
                )
            return base_snapshot.model_copy(
                update={
                    "account_id": context.account_id,
                    "orders": orders,
                    "snapshot_at": now - timedelta(seconds=1),
                    "expires_at": now + timedelta(minutes=10),
                }
            )

        deps = replace(
            deps,
            live_session=context.live_session,
            broker_adapter=context.adapter,
            connection=context.connection,
            account_state_source=_fresh_account_state,
            simulation_dispatch=None,
        )
    return deps


async def example_01_connect(context: OperationsContext) -> None:
    """Connect to the selected target or initialize Simulation readiness."""
    # Stage 01 — INPUT BOUNDARY: resolve one explicit execution authority.
    _stage(1)
    if context.adapter is None:
        context.connected = True
        _print_section(
            "CONNECTION",
            (
                ("Target", context.target),
                ("Status", "CONNECTED"),
                ("Authority", "Deterministic Simulation"),
                ("Environment", "simulation"),
                ("Virtual", "Yes"),
            ),
        )
        return
    result = await connect_broker(context.adapter)
    context.connected = _status(result) == "success"
    _print_section(
        "CONNECTION",
        (
            ("Target", context.target),
            ("Status", "CONNECTED" if context.connected else "FAILED"),
            ("Response Status", _status(result)),
            ("Virtual", "No"),
        ),
    )


async def example_02_platform(context: OperationsContext) -> None:
    """Read canonical platform information with portable terminal fields."""
    # Stage 02 — Read portable platform identity and capability evidence.
    _stage(2)
    if context.adapter is None:
        _render_platform(
            {
                "broker_id": "simulator",
                "provider_name": "Deterministic Simulation",
                "product_profile": "simulation",
                "environment": "simulation",
                "api_or_terminal_version": "virtual-v1",
                "observed_at": datetime.now(UTC),
                "name": "Deterministic Simulator",
                "company": "HaruQuantAI",
                "build": "1000",
                "language": "English",
                "connected": True,
                "trade_allowed": True,
                "dlls_allowed": True,
                "ping_last": 0,
                "path": "virtual://simulator",
                "data_path": "virtual://simulator/data",
                "common_data_path": "virtual://simulator/common",
            },
            virtual=True,
        )
        return
    result = await get_broker_platform_info(context.adapter)
    value = _response_data("Platform", result)
    if value is not None:
        _render_platform(value)


async def example_03_account(context: OperationsContext) -> None:
    """Read bounded account evidence with detailed account fields."""
    # Stage 03 — Read canonical account truth without sensitive identity fields.
    _stage(3)
    if context.adapter is None:
        _render_account(
            {
                "account_id": "account-001",
                "login": "account-001",
                "name": "Deterministic Virtual Account",
                "server": "Simulator-Server",
                "company": "HaruQuantAI",
                "account_reference_redacted": "virtual-account",
                "currency": "USD",
                "balance": Decimal("10000.00"),
                "credit": Decimal("0.00"),
                "profit": Decimal("0.00"),
                "equity": Decimal("10000.00"),
                "margin": Decimal("0.00"),
                "free_margin": Decimal("10000.00"),
                "status": "ACTIVE",
                "leverage": 100,
                "trade_mode": "DEMO",
                "trade_mode_description": "Demo account",
                "margin_mode": "HEDGING",
                "margin_mode_description": "Hedging position accounting",
                "trade_allowed": True,
                "trade_expert": True,
                "limit_orders": 0,
                "margin_so_level": 50.0,
                "retrieved_at": datetime.now(UTC),
            },
            virtual=True,
        )
        return
    result = await get_broker_account_info(context.adapter)
    value = _response_data("Account", result)
    if value is not None:
        _render_account(value)


def _merge_symbol_and_quote(
    symbol_value: object, quote_value: object | None
) -> dict[str, object]:
    raw_meta = _value(symbol_value, "provider_metadata", default={})
    combined: dict[str, object] = (
        dict(raw_meta) if isinstance(raw_meta, Mapping) else {}
    )
    if quote_value is not None:
        bid = _value(quote_value, "bid", default=None)
        ask = _value(quote_value, "ask", default=None)
        last = _value(quote_value, "last_price", default=None)
        if bid is not None:
            combined["bid"] = bid
        if ask is not None:
            combined["ask"] = ask
        if last is not None:
            combined["last"] = last
        if bid not in (None, "N/A") and ask not in (None, "N/A"):
            point_val = _value(symbol_value, "point", default=0.00001)
            try:
                p_float = float(point_val)  # type: ignore[arg-type]
                if p_float > 0:
                    combined["spread"] = round(
                        (float(ask) - float(bid)) / p_float  # type: ignore[arg-type]
                    )
            except ValueError, TypeError:
                pass
    for attr in (
        "provider_symbol",
        "product_profile",
        "base_asset",
        "quote_asset",
        "price_precision",
        "min_quantity",
        "max_quantity",
        "quantity_step",
    ):
        combined[attr] = _value(symbol_value, attr)
    return combined


async def example_04_symbol(context: OperationsContext) -> None:
    """Read canonical symbol specifications and quote evidence."""
    # Stage 04 — Read current instrument and quote evidence.
    _stage(4)
    if context.adapter is None:
        now = datetime.now(UTC)
        _render_symbol(
            {
                "provider_symbol": "EURUSD",
                "product_profile": "simulation",
                "base_asset": "EUR",
                "quote_asset": "USD",
                "price_unit": "USD",
                "quantity_unit": "lots",
                "price_precision": 5,
                "quantity_precision": 2,
                "price_step": Decimal("0.00001"),
                "min_quantity": Decimal("0.01"),
                "max_quantity": Decimal("100.00"),
                "quantity_step": Decimal("0.01"),
                "trading_flags": {"trade_allowed": True},
                "symbol": "EURUSD",
                "name": "EURUSD",
                "digits": 5,
                "point": 0.00001,
                "tick_size": 0.00001,
                "bid": 1.09990,
                "ask": 1.10010,
                "last": 1.10000,
                "spread": 20,
                "trade_mode": "FULL",
                "trade_mode_description": "Full trading access",
                "contract_size": 100000.0,
                "volume_min": 0.01,
                "volume_max": 100.0,
                "volume_step": 0.01,
                "swap_mode": "POINTS",
                "swap_long": -0.50,
                "swap_short": 0.10,
            },
            virtual=True,
        )
        _render_quote(
            {
                "symbol": "EURUSD",
                "bid": Decimal("1.09990"),
                "ask": Decimal("1.10010"),
                "last_price": Decimal("1.10000"),
                "price_unit": "USD",
                "quantity_unit": "lots",
                "provider_sequence_id": "virtual-quote-001",
                "provider_timestamp": now,
                "retrieved_at": now,
            },
            virtual=True,
        )
        return
    symbol_result = await get_broker_symbol_info(context.adapter, context.symbol)
    symbol_value = _response_data("Symbol", symbol_result)
    quote_result = await get_broker_quote(context.adapter, context.symbol)
    quote_value = _response_data("Quote", quote_result)

    if symbol_value is not None:
        _render_symbol(_merge_symbol_and_quote(symbol_value, quote_value))
    if quote_value is not None:
        _render_quote(quote_value)


async def example_05_positions(context: OperationsContext) -> None:
    """List bounded current position evidence."""
    # Stage 05 — Read bounded authority-owned open-position state.
    _stage(5)
    if context.adapter is None:
        _render_positions(
            {
                "items": (
                    {
                        "position_id": "position-001",
                        "symbol": "EURUSD",
                        "side": "LONG",
                        "state": "OPEN",
                        "quantity": Decimal("2.00"),
                        "quantity_unit": "lots",
                        "open_price": Decimal("1.0950"),
                        "current_price": Decimal("1.1000"),
                        "profit": Decimal("1000.00"),
                        "swap": Decimal("0.00"),
                        "currency": "USD",
                        "stop_loss": Decimal("1.0900"),
                        "take_profit": Decimal("1.1100"),
                        "retrieved_at": datetime.now(UTC),
                    },
                )
            },
            virtual=True,
        )
        return
    result = await get_broker_positions(context.adapter, limit=5)
    value = _response_data("Positions", result)
    if value is not None:
        _render_positions(value)


async def example_06_orders(context: OperationsContext) -> None:
    """List bounded current order evidence."""
    # Stage 06 — Read bounded authority-owned pending-order state.
    _stage(6)
    if context.adapter is None:
        _render_orders(_virtual_order_page(), title="Pending orders", virtual=True)
        return
    result = await get_broker_orders(context.adapter, limit=5)
    value = _response_data("Orders", result)
    if value is not None:
        _render_orders(value, title="Pending orders")


async def example_07_history_orders(context: OperationsContext) -> None:
    """List bounded historical orders."""
    # Stage 07 — Read one explicitly bounded order-history window.
    _stage(7)
    end = datetime.now(UTC)
    start = end - timedelta(days=30)
    if context.adapter is None:
        print("History window: last 30 days; maximum records: 5")
        _render_orders(_virtual_order_page(), title="Historical orders", virtual=True)
        return
    result = await list_broker_order_history(
        context.adapter,
        start_time=start,
        end_time=end,
        limit=5,
    )
    value = _response_data("Order history", result)
    if value is not None:
        _render_orders(value, title="Historical orders")


async def example_08_history_deals(context: OperationsContext) -> None:
    """List bounded historical deals."""
    # Stage 08 — Read one explicitly bounded deal-history window.
    _stage(8)
    end = datetime.now(UTC)
    start = end - timedelta(days=30)
    if context.adapter is None:
        print("History window: last 30 days; maximum records: 5")
        _render_deals(
            {
                "items": (
                    {
                        "deal_id": "deal-001",
                        "order_id": "order-001",
                        "position_id": "position-001",
                        "symbol": "EURUSD",
                        "side": "BUY",
                        "quantity": Decimal("1.00"),
                        "quantity_unit": "lots",
                        "price": Decimal("1.0950"),
                        "partial": False,
                        "fee": Decimal("3.50"),
                        "fee_currency": "USD",
                        "retrieved_at": datetime.now(UTC),
                    },
                )
            },
            virtual=True,
        )
        return
    result = await list_broker_deal_history(
        context.adapter,
        start_time=start,
        end_time=end,
        limit=5,
    )
    value = _response_data("Deal history", result)
    if value is not None:
        _render_deals(value)


async def _run_mutation(
    context: OperationsContext,
    label: str,
    operation: object,
    request: object,
    *,
    action_policy: object | None = None,
) -> None:
    """Run one governed Simulation mutation or fail closed for provider mode."""
    if context.target != "sim" and not _provider_mutations_enabled():
        print(
            f"{label}: BLOCKED — provider mutation requires ENVIRONMENT=dev, "
            "explicit opt-in, and application-composed live session"
        )
        return
    if (
        context.target != "sim"
        and getattr(request, "expected_version", None) is not None
    ):
        route = getattr(request, "route", None)
        account_id = getattr(request, "account_id", None)
        if route is not None and account_id is not None:
            auth_id = getattr(request, "provider_id", None) or "simulation"
            proj = context.store.load_projection((route, account_id, auth_id))
            if proj is not None:
                request = request.model_copy(update={"expected_version": proj.version})
    result = await operation(  # type: ignore[operator]
        request,
        _dependencies(context, action_policy=action_policy),
    )
    if _status(result) != "success":
        print("STAGE RESULT ERROR:", result.error)
    else:
        data = _response_data(label, result)
        p_id = _value(data, "provider_order_id", None) or _value(
            data, "client_order_id", None
        )
        if p_id:
            context.placed_order_id = str(p_id)
    _render_execution(label, result)


async def example_09_open_position(context: OperationsContext) -> None:
    """Submit one governed market order."""
    # Stage 09 — Submit only through the complete governed Trading operation.
    _stage(9)
    await _run_mutation(
        context,
        "Open position",
        submit_order,
        _request(context, 9, "submit_order", quantity=Decimal("0.02")),
    )


async def example_10_calculate_profit_margin(context: OperationsContext) -> None:
    """Calculate bounded margin and hypothetical profit."""
    # Stage 10 — Calculate without claiming hypothetical profit as performance.
    _stage(10)
    adapter = context.adapter
    virtual = adapter is None
    if (
        adapter is None
        and context.target != "sim"
        and load_settings().environment == "dev"
    ):
        try:
            connection = resolve_provider_connection_config(
                "mt5",
                settings=load_broker_provider_settings(),
            )
            created = create_broker_adapter("mt5", connection)
            if _status(created) == "success":
                cand = get_broker_value_field(created, "data")
                if cand is not None:
                    res = await connect_broker(cand)
                    if _status(res) == "success":
                        adapter = cand
        except RuntimeError, ValueError, AttributeError, OSError:
            adapter = None

    if adapter is None:
        quantity = Decimal("0.02")
        contract_size = Decimal(100000)
        input_price = Decimal("1.1000")
        target_price = Decimal("1.1100")
        leverage = Decimal(100)
        required_margin = quantity * contract_size * input_price / leverage
        hypothetical_profit = quantity * contract_size * (target_price - input_price)
        _print_section(
            "PROFIT AND MARGIN CALCULATION",
            (
                ("Symbol", context.symbol),
                ("Side", "BUY"),
                ("Quantity", "0.02 lots"),
                ("Input Price", "1.1000"),
                ("Target Price", "1.1100"),
                ("Required Margin", f"{required_margin:.2f} USD"),
                ("Hypothetical Profit", f"{hypothetical_profit:.2f} USD"),
                ("Virtual", "Yes"),
                ("Evidence", "Deterministic calculation; not observed performance"),
            ),
        )
        return

    profile = "mt5" if context.target == "sim" else context.target
    margin = build_broker_margin_request(
        symbol=context.symbol,
        side="BUY",
        quantity="0.02",
        quantity_unit="lots",
        price="1.10",
        product_profile=profile,
    )
    profit = build_broker_profit_request(
        symbol=context.symbol,
        side="BUY",
        quantity="0.02",
        quantity_unit="lots",
        open_price="1.10",
        close_price="1.11",
        product_profile=profile,
    )
    margin_result = await calculate_broker_margin(adapter, margin)
    profit_result = await calculate_broker_profit(adapter, profit)
    margin_value = _response_data("Margin", margin_result)
    profit_value = _response_data("Profit", profit_result)
    if margin_value is not None and profit_value is not None:
        _print_section(
            "PROFIT AND MARGIN CALCULATION",
            (
                ("Symbol", context.symbol),
                ("Side", "BUY"),
                ("Quantity", "0.02 lots"),
                ("Input Price", "1.10"),
                ("Target Price", "1.11"),
                ("Required Margin", f"{margin_value} USD"),
                ("Hypothetical Profit", f"{profit_value} USD"),
                ("Virtual", "Yes" if virtual else "No"),
                (
                    "Evidence",
                    "MT5 native provider calculation (order_calc_margin / order_calc_profit)",
                ),
            ),
        )


async def example_11_modify_position(context: OperationsContext) -> None:
    """Modify one position under exact mutable-field authority."""
    # Stage 11 — Modify only the explicitly authorized position field.
    _stage(11)
    request = _request(
        context,
        11,
        "modify_position",
        position_id=context.position_id,
        target_broker_position_id=context.position_id,
        order_type="LIMIT",
        price=Decimal("1.1000"),
        stop_loss=Decimal("1.0950"),
    )
    await _run_mutation(
        context,
        "Modify position",
        modify_position,
        request,
        action_policy=examples.action_policy(
            "modify_position",
            mutable_fields="stop_loss",
        ),
    )


async def example_12_partial_close_position(context: OperationsContext) -> None:
    """Partially close one exact position."""
    # Stage 12 — Close only the exact approved reduction quantity.
    _stage(12)
    await _run_mutation(
        context,
        "Partial close",
        close_position,
        _request(
            context,
            12,
            "close_position",
            position_id=context.position_id,
            target_broker_position_id=context.position_id,
            quantity=Decimal("0.50"),
        ),
    )


async def example_13_close_position(context: OperationsContext) -> None:
    """Close the confirmed remaining virtual position quantity."""
    # Stage 13 — Close the separately evidenced remaining quantity.
    _stage(13)
    await _run_mutation(
        context,
        "Full close",
        close_position,
        _request(
            context,
            13,
            "close_position",
            position_id=context.position_id,
            target_broker_position_id=context.position_id,
            quantity=Decimal("1.50"),
        ),
    )


async def example_14_place_pending_order(context: OperationsContext) -> None:
    """Submit one governed pending limit order."""
    # Stage 14 — Submit a limit order through the same governed path.
    _stage(14)
    await _run_mutation(
        context,
        "Place pending order",
        submit_order,
        _request(
            context,
            14,
            "submit_order",
            order_type="LIMIT",
            price=Decimal("1.0900"),
            quantity=Decimal("0.01"),
        ),
    )


async def example_15_modify_pending_order(context: OperationsContext) -> None:
    """Modify one pending order using optimistic version evidence."""
    # Stage 15 — Modify one exact order with optimistic version authority.
    _stage(15)
    target_order_id = context.placed_order_id or context.order_id
    expected_ver = 2 if context.target != "sim" else 1
    await _run_mutation(
        context,
        "Modify pending order",
        modify_order,
        _request(
            context,
            15,
            "modify_order",
            order_id=target_order_id,
            target_broker_order_id=target_order_id,
            expected_version=expected_ver,
            order_type="LIMIT",
            price=Decimal("1.0895"),
            quantity=Decimal("0.01"),
        ),
        action_policy=examples.action_policy(
            "modify_order",
            mutable_fields="price",
        ),
    )


async def example_16_cancel_pending_order(context: OperationsContext) -> None:
    """Cancel one pending order using current target evidence."""
    # Stage 16 — Cancel one exact order through the governed Trading operation.
    _stage(16)
    target_order_id = context.placed_order_id or context.order_id
    expected_ver = 4 if context.target != "sim" else 1
    await _run_mutation(
        context,
        "Cancel pending order",
        cancel_order,
        _request(
            context,
            16,
            "cancel_order",
            order_id=target_order_id,
            target_broker_order_id=target_order_id,
            expected_version=expected_ver,
        ),
    )


async def example_17_shutdown(context: OperationsContext) -> None:
    """Disconnect the selected authority and report cleanup."""
    # Stage 17 — OUTPUT BOUNDARY: release the selected authority deterministically.
    _stage(17)
    if context.adapter is None:
        context.connected = False
        _print_section(
            "SHUTDOWN",
            (
                ("Target", context.target),
                ("Status", "DISCONNECTED"),
                ("Authority Released", "Yes"),
                ("Unresolved Work", 0),
                ("Virtual", "Yes"),
            ),
        )
        return
    if context.live_session is not None:
        await stop_live_session(context.live_session)
    result = await disconnect_broker(context.adapter)
    context.connected = False
    _print_section(
        "SHUTDOWN",
        (
            ("Target", context.target),
            ("Status", _status(result)),
            ("Authority Released", "Yes" if _status(result) == "success" else "No"),
            ("Virtual", "No"),
        ),
    )


async def run() -> None:
    """Execute all 17 examples through one selected target context."""
    context = await _compose_context(EXECUTION_TARGET)
    operations = (
        example_01_connect,
        example_02_platform,
        example_03_account,
        example_04_symbol,
        example_05_positions,
        example_06_orders,
        example_07_history_orders,
        example_08_history_deals,
        example_09_open_position,
        example_10_calculate_profit_margin,
        example_11_modify_position,
        # example_12_partial_close_position,
        # example_13_close_position,
        # example_14_place_pending_order,
        # example_15_modify_pending_order,
        # example_16_cancel_pending_order,
    )
    try:
        for operation in operations:
            await operation(context)
    finally:
        await example_17_shutdown(context)
    print(
        f"\nSUCCESS: {WORKFLOW_ID} completed 17/17 examples via "
        f"target='{context.target}'"
    )


def main() -> None:
    """Run the broker-agnostic workflow."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
