"""Executable Trading contracts usage example.

Demonstrates FEAT-TRD-01 public Trading contracts, route selection, and validation.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any, NamedTuple

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import build_provider_specification_snapshot
from app.services.trading import (
    create_execution_receipt,
    create_legacy_compatible_trading_request,
    create_order_intent,
    create_order_intent_v2,
    create_portfolio_rebalance_execution_request,
    create_trade_record,
    create_trading_action_draft,
    create_trading_error,
    create_trading_request,
    create_trading_request_v2,
    get_public_contracts,
    get_trading_contract_version,
    get_trading_route,
    map_trading_error,
    redact_trading_payload,
)
from app.utils import (
    build_response_metadata,
    canonical_json,
    success_response,
)

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)
ExecutionReceipt = Any


class _SymbolInfo(NamedTuple):
    """Minimal verified MT5-shaped provider specification fixture."""

    name: object = "EURUSD"
    digits: object = 5
    point: object = 0.00001
    filling_mode: object = 3
    order_mode: object = 15
    expiration_mode: object = 15
    order_gtc_mode: object = 0
    trade_exemode: object = 2
    trade_mode: object = 4
    trade_calc_mode: object = 0
    swap_mode: object = 1
    swap_rollover3days: object = 3
    trade_stops_level: object = 0
    trade_freeze_level: object = 0
    volume_min: object = 0.01
    volume_max: object = 100.0
    volume_step: object = 0.01
    volume_limit: object = 0.0
    trade_tick_size: object = 0.00001
    trade_tick_value: object = 1.0
    trade_tick_value_profit: object = 1.0
    trade_tick_value_loss: object = 1.0
    trade_contract_size: object = 100000.0
    currency_base: object = "EUR"
    currency_profit: object = "USD"
    currency_margin: object = "USD"
    margin_initial: object = 0.0
    margin_maintenance: object = 0.0
    margin_hedged: object = 100000.0
    margin_hedged_use_leg: object = False
    swap_long: object = -0.2
    swap_short: object = -1.2


def _provider_specification() -> object:
    """Build one transport-free typed provider snapshot through Brokers."""
    return build_provider_specification_snapshot(
        symbol_info=_SymbolInfo(),
        broker="mt5",
        server="DemoServer",
        account_id="usage-account-001",
        environment="demo",
        terminal_build="4410",
        source_revision="mt5:4410",
        observed_at=NOW,
        account_info=None,
    )


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


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


def _request_data() -> dict[str, object]:
    """Build complete canonical request material for usage examples."""
    return {
        "request_id": "req-11111111-1111-4111-8111-111111111111",
        "workflow_id": "wf-22222222-2222-4222-8222-222222222222",
        "correlation_id": "cor-33333333-3333-4333-8333-333333333333",
        "route": "sim",
        "action": "submit_order",
        "provider_id": None,
        "account_id": "usage-account-001",
        "strategy_id": "usage-strategy-001",
        "strategy_version": "v1",
        "intent_id": "usage-source-intent-001",
        "symbol": "EURUSD",
        "side": "BUY",
        "order_type": "MARKET",
        "quantity_unit": "units",
        "quantity": "1.00",
        "risk_decision_id": "usage-risk-001",
        "action_policy_verdict_id": "usage-verdict-001",
        "approval_token_ref": "usage-approval-001",
        "idempotency_key": "usage-idempotency-001",
        "canonical_material_version": "v1",
        "system_time": NOW,
        "valid_until": NOW + timedelta(minutes=5),
    }


def _receipt() -> ExecutionReceipt:
    """Build a confirmed simulator receipt for usage examples."""
    return create_execution_receipt(
        receipt_id="usage-receipt-001",
        intent_id="usage-intent-001",
        client_order_id="usage-order-001",
        route=get_trading_route("sim"),
        authority="simulator",
        provider_order_id="sim-order-001",
        status="filled",
        requested_quantity=Decimal("1.00"),
        filled_quantity=Decimal("1.00"),
        average_price=Decimal("1.10000"),
        authority_timestamp=NOW,
        received_at=NOW,
        response_classification="confirmed",
        retry_safe=False,
        reconciliation_required=False,
        request_id="req-11111111-1111-4111-8111-111111111111",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )


def _rebalance_data() -> dict[str, object]:
    """Build a canonically bound portfolio rebalance request."""
    data: dict[str, object] = {
        "contract_version": "v1",
        "schema_id": "trading.portfolio_rebalance_execution_request.v1",
        "request_id": "req-77777777-7777-4777-8777-777777777777",
        "workflow_id": "wf-22222222-2222-4222-8222-222222222222",
        "correlation_id": "cor-33333333-3333-4333-8333-333333333333",
        "plan_id": "usage-plan-001",
        "plan_version": "v1",
        "portfolio_id": "usage-portfolio-001",
        "allocation_version": "allocation-v1",
        "allocation_decision_id": "usage-allocation-decision-001",
        "eligibility_decision_ids": ("usage-eligibility-001",),
        "actions": (
            {
                "action_id": "usage-action-001",
                "component_id": "usage-strategy-001",
                "eligibility_decision_id": "usage-eligibility-001",
                "action": "reduce_exposure",
                "reduce_only": True,
                "current_exposure": "0.50",
                "target_exposure": "0.25",
                "reduction_amount": "0.25",
            },
        ),
        "route": get_trading_route("sim"),
        "approval_token_ref": "usage-approval-001",
        "canonical_material_version": "v1",
        "valid_from": NOW,
        "valid_until": NOW + timedelta(minutes=5),
    }
    data["canonical_hash"] = sha256(canonical_json(data).encode()).hexdigest()
    return data


def fr_trd_001() -> None:
    """FR-TRD-001: Stage 1 — Expose only sim, paper, and live action routes."""
    _header("Stage 1: Route Selection - Supported Action Routes (FR-TRD-001)")
    route = get_trading_route("paper")
    print(_format_result(route))
    print(f"Data -> route='{route.value}'")


def fr_trd_002() -> None:
    """FR-TRD-002: Stage 1 — Validate immutable canonical request."""
    _header("Stage 1: Request Validation - Canonical Trading Request (FR-TRD-002)")
    request = create_trading_request(**_request_data())
    print(_format_result(request))
    print(
        f"Data -> request_id='{request.request_id}', action='{request.action}', route='{request.route}'"
    )


def fr_trd_003() -> None:
    """FR-TRD-003: Stage 3 — Return finite JSON-safe envelope."""
    _header("Stage 3: Response Envelope - Standard JSON Response (FR-TRD-003)")
    envelope = success_response(
        {"route": "sim"},
        message="Trading contract validated",
        metadata=build_response_metadata(
            name="trading.usage_contract",
            domain="trading",
            risk_level="low",
            request_id="req-11111111-1111-4111-8111-111111111111",
            start_time=1,
            read_only=True,
            writes_file=False,
            modifies_database=False,
            places_trade=False,
            requires_network=False,
        ),
    )
    print(_format_result(envelope))
    print(f"Data -> status='{envelope.status}', message='{envelope.message}'")


def fr_trd_004() -> None:
    """FR-TRD-004: Stage 3 — Expose deterministic OrderIntent v1."""
    _header("Stage 3: Order Intent - Construct OrderIntent v1 (FR-TRD-004)")
    intent = create_order_intent(
        client_order_id="usage-order-001",
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        route=get_trading_route("sim"),
        provider_id=None,
        account_id="usage-account-001",
        strategy_id="usage-strategy-001",
        strategy_version="v1",
        source_intent_id="usage-source-intent-001",
        symbol="EURUSD",
        action="submit_order",
        side="BUY",
        order_type="MARKET",
        quantity_unit="units",
        approved_volume=Decimal("1.00"),
        risk_approved_volume=Decimal("1.00"),
        idempotency_hash="b" * 64,
        canonical_material_version="v1",
        risk_decision_id="usage-risk-001",
        action_policy_verdict_id="usage-verdict-001",
        approval_token_ref="usage-approval-001",
        created_at=NOW,
        valid_until=NOW + timedelta(minutes=5),
    )
    print(_format_result(intent))
    print(
        f"Data -> client_order_id='{intent.client_order_id}', approved_volume={intent.approved_volume}"
    )


def fr_trd_005() -> None:
    """FR-TRD-005: Stage 3 — Expose immutable ExecutionReceipt v1."""
    _header("Stage 3: Execution Receipt - Construct ExecutionReceipt v1 (FR-TRD-005)")
    receipt = _receipt()
    print(_format_result(receipt))
    print(
        f"Data -> receipt_id='{receipt.receipt_id}', status='{receipt.status}', filled_quantity={receipt.filled_quantity}"
    )


def fr_trd_006() -> None:
    """FR-TRD-006: Stage 3 — Expose TradeRecord v1 without derived analytics metrics."""
    _header("Stage 3: Trade Record - Construct TradeRecord v1 (FR-TRD-006)")
    record = create_trade_record(
        record_id="usage-record-001",
        receipt=_receipt(),
        fill_ids=("usage-fill-001",),
        authority_state="confirmed",
        reconciliation_state="reconciled",
        created_at=NOW,
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )
    print(_format_result(record))
    print(
        f"Data -> record_id='{record.record_id}', reconciliation_state='{record.reconciliation_state}'"
    )


def fr_trd_007() -> None:
    """FR-TRD-007: Stage 2 — Expose finite Trading exception with registered code."""
    _header("Stage 2: Error Taxonomy - Create Trading Domain Error (FR-TRD-007)")
    error = create_trading_error("INVALID_REQUEST", "Request evidence is invalid")
    print(_format_result(error))
    print(f"Data -> trading_code='{error.trading_code}', detail='{error.detail}'")


def fr_trd_008() -> None:
    """FR-TRD-008: Stage 2 — Map failures into canonical envelope without raw exceptions."""
    _header("Stage 2: Exception Mapping - Map Raw Exception (FR-TRD-008)")
    mapped = map_trading_error(
        TimeoutError("provider detail"),
        {
            "operation": "submit_order",
            "request_id": "req-11111111-1111-4111-8111-111111111111",
        },
    )
    print(_format_result(mapped))
    print(f"Data -> status='{mapped.status}', message='{mapped.message}'")


def fr_trd_009() -> None:
    """FR-TRD-009: Stage 2 — Recursively redact secrets before returning payloads."""
    _header("Stage 2: Secret Redaction - Redact Sensitive Payload (FR-TRD-009)")
    redacted = redact_trading_payload({"credentials": {"api_key": "secret"}})
    print(_format_result(redacted))
    print(f"Data -> redacted_keys={list(redacted.data.keys())}")


def fr_trd_010() -> None:
    """FR-TRD-010: Stage 3 — Return exact stable Python API metadata."""
    _header("Stage 3: Public API Metadata - Discover Registered Contracts (FR-TRD-010)")
    contracts = get_public_contracts()
    print(_format_result(contracts))
    print(f"Data -> public_contracts_count={len(contracts.data or ())}")


def fr_trd_012() -> None:
    """FR-TRD-012: Stage 1 — Create non-executable action draft."""
    _header(
        "Stage 1: Action Drafting - Create Non-Executable Action Draft (FR-TRD-012)"
    )
    draft = create_trading_action_draft(_request_data())
    print(_format_result(draft))
    print(f"Data -> draft_status='{draft.status}'")


def fr_trd_063() -> None:
    """FR-TRD-063: Stage 3 — Expose PortfolioRebalanceExecutionRequest v1."""
    _header(
        "Stage 3: Portfolio Rebalance Request - Construct Rebalance Request (FR-TRD-063)"
    )
    rebalance = create_portfolio_rebalance_execution_request(**_rebalance_data())
    print(_format_result(rebalance))
    print(
        f"Data -> plan_id='{rebalance.plan_id}', portfolio_id='{rebalance.portfolio_id}'"
    )


def fr_trd_066() -> None:
    """FR-TRD-066: Stage 1 — Expose canonical TRADING_CONTRACT_VERSION constant."""
    _header(
        "Stage 1: Version Constant - Inspect Contract Version Constant (FR-TRD-066)"
    )
    version = get_trading_contract_version()
    print("Output Result -> str : str")
    print(f"Data -> version='{version}'")


def fr_trd_097() -> None:
    """FR-TRD-097: construct a request with independent fill and time policy."""
    request = create_trading_request_v2(
        provider_specification=_provider_specification(),
        fill_policy="FOK",
        time_policy="GTC",
        **_request_data(),
    )
    print("Data ->", request.contract_version, request.fill_policy, request.time_policy)


def fr_trd_098() -> None:
    """FR-TRD-098: bind policies to the exact provider revision."""
    request = create_trading_request_v2(
        provider_specification=_provider_specification(),
        fill_policy="IOC",
        time_policy="DAY",
        **_request_data(),
    )
    print("Data -> provider_revision", request.provider_specification_checksum[:12])


def fr_trd_099() -> None:
    """FR-TRD-099: preserve explicit UTC SPECIFIED_DAY expiration."""
    request = create_trading_request_v2(
        provider_specification=_provider_specification(),
        fill_policy="FOK",
        time_policy="SPECIFIED_DAY",
        expiration=NOW + timedelta(days=1),
        **_request_data(),
    )
    print("Data -> expiration", request.expiration.isoformat())


def fr_trd_100() -> None:
    """FR-TRD-100: label explicit v1 compatibility as parity-ineligible."""
    request = create_legacy_compatible_trading_request(
        legacy_profile_version="trading-order-policy-legacy-v1",
        provider_specification=_provider_specification(),
        **_request_data(),
    )
    print("Data -> legacy", request.legacy_compatibility)


def fr_trd_112() -> None:
    """FR-TRD-112: construct an executable v2 intent with both policies."""
    intent = create_order_intent_v2(
        provider_specification=_provider_specification(),
        fill_policy="IOC",
        time_policy="GTC",
        client_order_id="trd-usage-v2",
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        route="sim",
        provider_id=None,
        account_id="usage-account-001",
        strategy_id="usage-strategy-001",
        strategy_version="v1",
        source_intent_id="usage-source-intent-v2",
        symbol="EURUSD",
        action="submit_order",
        side="BUY",
        order_type="MARKET",
        quantity_unit="units",
        approved_volume=Decimal(1),
        risk_approved_volume=Decimal(1),
        idempotency_hash="c" * 64,
        canonical_material_version="v2",
        risk_decision_id="usage-risk-001",
        action_policy_verdict_id="usage-verdict-001",
        approval_token_ref="usage-approval-001",
        created_at=NOW,
        valid_until=NOW + timedelta(minutes=5),
    )
    print("Data ->", intent.contract_version, intent.fill_policy, intent.time_policy)


def _emit_requirement_success(function: object) -> object:
    """Wrap one example so direct execution emits its success contract."""

    def wrapped() -> None:
        function()
        requirement = function.__name__.removeprefix("fr_trd_").replace("_", "-")
        print(f"SUCCESS: FR-TRD-{requirement}")

    return wrapped


for _example_name, _example_function in tuple(globals().items()):
    if _example_name.startswith("fr_trd_") and callable(_example_function):
        globals()[_example_name] = _emit_requirement_success(_example_function)


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-TRD-01 — contracts/ — Canonical Contracts and Registries\n\n"
        "Purpose: Declare and validate all Trading domain request, response, order intent, receipt, trade record, error, and contract metadata DTOs.\n\n"
        "Module flow:\n"
        "-> Stage 1: Route selection, action drafting, and input parameter definition\n"
        "-> Stage 2: Fail-closed validation, error classification, mapping, and redaction\n"
        "-> Stage 3: Immutable contract payload construction and response envelping"
    )

    # Stage 1: Route selection & Action drafting
    fr_trd_001()
    fr_trd_012()
    fr_trd_066()
    fr_trd_097()
    fr_trd_098()
    fr_trd_099()
    fr_trd_100()
    fr_trd_112()

    # Stage 2: Fail-closed validation & Error handling
    fr_trd_002()
    fr_trd_007()
    fr_trd_008()
    fr_trd_009()

    # Stage 3: Immutable contract construction & Response envelopes
    fr_trd_003()
    fr_trd_004()
    fr_trd_005()
    fr_trd_006()
    fr_trd_010()
    fr_trd_063()


if __name__ == "__main__":
    main()
