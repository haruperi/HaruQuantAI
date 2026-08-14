"""Integration tests for parity relationship-graph mutation detection."""

from typing import Any

from app.services.simulator import (
    compare_parity_evidence,
    get_parity_envelope,
)

_ENVELOPE = get_parity_envelope("v1")


def paired_evidence() -> tuple[dict[str, object], dict[str, object]]:
    """Return one semantically paired (sim-shaped, provider-shaped) evidence pair.

    The two sides carry different raw identifiers and different provider
    observation timestamps; they are alpha-equivalent on every economic,
    gate, and relationship dimension.
    """
    left: dict[str, object] = {
        "certificate_target": "demo",
        "evaluation_time": "2026-08-20T12:00:00+00:00",
        "identity": {
            "execution_model_hash": "e" * 64,
            "config_hash": "c" * 64,
            "source_lineage_hash": "s" * 64,
            "tick_lineage_hash": "t" * 64,
            "market_evidence_class": "genuine_bid_ask_ticks",
        },
        "initial_authority_state": {
            "state_hash": "f" * 64,
            "exclusive_account": True,
            "foreign_activity_event_count": 0,
        },
        "gates": (
            {
                "role": "risk_approval",
                "order": 0,
                "inputs": {"symbol": "EURUSD"},
                "outcome": "approved",
            },
            {
                "role": "live_mutation_authorization",
                "order": 1,
                "inputs": {},
                "outcome": "require_allow_live_mutations_true",
                "route": "live",
                "route_specific": True,
                "route_policy": "require_allow_live_mutations_true",
            },
            {
                "role": "pre_mutation_audit",
                "order": 2,
                "inputs": {},
                "outcome": "audit_failed_stops_dispatch",
                "route": "live",
                "route_specific": True,
                "route_policy": "audit_failed_stops_dispatch",
            },
            {
                "role": "adapter_capability_validation",
                "order": 3,
                "inputs": {},
                "outcome": "validate_adapter_capability_exact_match",
                "route": "paper",
                "route_specific": True,
                "route_policy": "validate_adapter_capability_exact_match",
            },
        ),
        "orders": (
            {
                "order_id": "ord-1",
                "client_order_id": "co-1",
                "symbol": "EURUSD",
                "side": "BUY",
                "order_type": "MARKET",
                "state": "FILLED",
                "quantity": "0.1",
                "filled": "0.1",
                "placed_at": "2026-08-20T11:00:00+00:00",
                "provider_timestamp": "2026-08-20T11:00:01+00:00",
            },
        ),
        "deals": (
            {
                "deal_id": "dl-1",
                "order_id": "ord-1",
                "position_id": "pos-1",
                "entry": "IN",
                "reason": "FILL",
                "quantity": "0.1",
                "price": "1.1050",
                "executed_at": "2026-08-20T11:00:01+00:00",
            },
        ),
        "positions": (
            {
                "position_id": "pos-1",
                "symbol": "EURUSD",
                "side": "LONG",
                "quantity": "0.1",
                "state": "OPEN",
                "profit": "5",
                "opened_at": "2026-08-20T11:00:01+00:00",
            },
        ),
        "receipts": (
            {
                "receipt_id": "rc-1",
                "intent_id": "in-1",
                "client_order_id": "co-1",
                "route": "sim",
                "status": "filled",
                "requested_quantity": "0.1",
                "filled_quantity": "0.1",
                "average_price": "1.1050",
                "authority_timestamp": "2026-08-20T11:00:01+00:00",
                "received_at": "2026-08-20T11:00:02+00:00",
                "response_classification": "confirmed",
                "retry_safe": False,
                "reconciliation_required": False,
                "provider_order_id": "po-1",
                "provider_deal_ids": ["dl-1"],
            },
        ),
        "events": (
            {
                "event_id": "ev-1",
                "event_type": "order_accepted",
                "occurred_at": "2026-08-20T11:00:00+00:00",
                "source_sequence": 0,
            },
            {
                "event_id": "ev-2",
                "event_type": "order_outcome",
                "occurred_at": "2026-08-20T11:00:01+00:00",
                "causes": ["ev-1"],
                "source_sequence": 1,
            },
        ),
        "ledger": {
            "initial_balance": "10000",
            "final_balance": "10005",
            "final_equity": "10005",
            "unrealized_profit": "0",
            "postings": (
                {
                    "posting_id": "p1",
                    "kind": "realized_profit",
                    "amount": "5",
                    "occurred_at": "2026-08-20T11:00:01+00:00",
                    "source_sequence": 0,
                },
            ),
        },
    }
    right: dict[str, Any] = {
        **left,
        "orders": (
            {
                **left["orders"][0],  # type: ignore[index]
                "order_id": "MT-ORD-9",
                "client_order_id": "MT-CO-9",
                "provider_timestamp": "2026-08-20T11:00:05+00:00",
            },
        ),
        "deals": (
            {
                **left["deals"][0],  # type: ignore[index]
                "deal_id": "MT-DEAL-9",
                "order_id": "MT-ORD-9",
            },
        ),
        "positions": (
            {
                **left["positions"][0],  # type: ignore[index]
                "position_id": "MT-POS-9",
            },
        ),
        "receipts": (
            {
                **left["receipts"][0],  # type: ignore[index]
                "receipt_id": "MT-RC-9",
                "intent_id": "MT-IN-9",
                "client_order_id": "MT-CO-9",
                "provider_order_id": "MT-PO-9",
                "provider_deal_ids": ["MT-DEAL-9"],
                "route": "paper",
            },
        ),
        "events": (
            {
                **left["events"][0],  # type: ignore[index]
                "event_id": "MT-EV-1",
            },
            {
                **left["events"][1],  # type: ignore[index]
                "event_id": "MT-EV-2",
                "causes": ["MT-EV-1"],
            },
        ),
        "ledger": {
            **left["ledger"],  # type: ignore[index]
            "postings": (
                {
                    **left["ledger"]["postings"][0],  # type: ignore[index]
                    "posting_id": "MT-P1",
                },
            ),
        },
    }
    right["deals"][0]["position_id"] = "MT-POS-9"
    return left, right


def test_relationship_mutation_fails_parity() -> None:
    """Standing regression: an order/deal/position relationship mutation fails."""
    left, right = paired_evidence()
    mutated_positions: list[Any] = list(right["positions"])  # type: ignore[call-overload]
    mutated_positions.append(
        {
            "position_id": "MT-POS-10",
            "symbol": "EURUSD",
            "side": "LONG",
            "quantity": "0.1",
            "state": "OPEN",
            "profit": "0",
            "opened_at": "2026-08-20T11:00:01+00:00",
        }
    )
    mutated_deals: list[Any] = list(right["deals"])  # type: ignore[call-overload]
    mutated_deals[0] = {**mutated_deals[0], "position_id": "MT-POS-10"}
    right["positions"] = tuple(mutated_positions)  # type: ignore[assignment]
    right["deals"] = tuple(mutated_deals)  # type: ignore[assignment]
    result = compare_parity_evidence(left, right, _ENVELOPE)
    assert result["passed"] is False
    assert any("order.linkage_graph" in f for f in result["failures"])


def test_causal_edge_mutation_fails_parity() -> None:
    """A dropped causal edge between paired events fails the comparison."""
    left, right = paired_evidence()
    mutated_events: list[Any] = list(right["events"])  # type: ignore[call-overload]
    mutated_events[1] = {**mutated_events[1], "causes": ()}
    right["events"] = tuple(mutated_events)  # type: ignore[assignment]
    result = compare_parity_evidence(left, right, _ENVELOPE)
    assert result["passed"] is False
    assert any("causal.evidenced_partial_order" in f for f in result["failures"])


def test_renamed_identifiers_preserve_cardinality() -> None:
    """FR-SIM-238: renaming preserves identifier cardinality and links."""
    left, right = paired_evidence()
    result = compare_parity_evidence(left, right, _ENVELOPE)
    assert result["passed"] is True, result["failures"]
    graph = result["relationship_map"]
    assert len(graph["deals"]) == 1  # type: ignore[arg-type]
    # Events rename to a8 (cause) and a9 (effect) in encounter order after
    # order, receipt, position, and deal identifiers.
    assert graph["causal_edges"] == [["a8", "a9"]]  # type: ignore[index]
