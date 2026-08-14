"""Unit tests for the relationship-preserving parity evidence normalizer."""

import pytest
from app.services.simulator import (
    get_parity_envelope,
    normalize_parity_evidence,
)
from app.services.simulator.errors import SimulationError
from app.services.simulator.parity.envelope import load_parity_envelope
from app.services.simulator.parity.normalize import normalize_parsed_evidence

_ENVELOPE = get_parity_envelope("v1")


def _evidence() -> dict[str, object]:
    return {
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
        "gates": [],
        "orders": [
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
            }
        ],
        "deals": [
            {
                "deal_id": "dl-1",
                "order_id": "ord-1",
                "position_id": "pos-1",
                "entry": "IN",
                "reason": "FILL",
                "quantity": "0.1",
                "price": "1.1050",
                "executed_at": "2026-08-20T11:00:01+00:00",
            }
        ],
        "positions": [
            {
                "position_id": "pos-1",
                "symbol": "EURUSD",
                "side": "LONG",
                "quantity": "0.1",
                "state": "OPEN",
                "profit": "5",
                "opened_at": "2026-08-20T11:00:01+00:00",
            }
        ],
        "receipts": [
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
            }
        ],
        "events": [
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
        ],
        "ledger": {
            "initial_balance": "10000",
            "final_balance": "10005",
            "final_equity": "10005",
            "unrealized_profit": "0",
            "postings": [
                {
                    "posting_id": "p1",
                    "kind": "realized_profit",
                    "amount": "5",
                    "occurred_at": "2026-08-20T11:00:01+00:00",
                    "source_sequence": 0,
                }
            ],
        },
    }


def test_alpha_renamed_equivalent_graphs_hash_identically() -> None:
    """FR-SIM-238: renamed-but-equivalent graphs normalize identically."""
    left = _evidence()
    right = _evidence()
    right["orders"][0]["order_id"] = "ORD-X"  # type: ignore[index]
    right["orders"][0]["client_order_id"] = "CO-X"  # type: ignore[index]
    right["deals"][0]["order_id"] = "ORD-X"  # type: ignore[index]
    receipts = right["receipts"][0]  # type: ignore[index]
    receipts["client_order_id"] = "CO-X"
    receipts["provider_order_id"] = "PO-X"
    left_view = normalize_parity_evidence(left, _ENVELOPE)
    right_view = normalize_parity_evidence(right, _ENVELOPE)
    assert left_view["canonical_digest"] == right_view["canonical_digest"]
    assert left_view["identifier_map"] != right_view["identifier_map"]


def test_broken_foreign_key_fails_closed() -> None:
    """FR-SIM-238: a reference to an undefined identifier fails closed."""
    evidence = _evidence()
    evidence["deals"][0]["position_id"] = "missing-position"  # type: ignore[index]
    with pytest.raises(SimulationError) as raised:
        normalize_parity_evidence(evidence, _ENVELOPE)
    assert raised.value.code == "SIM_INTEGRITY_FAILURE"


def test_reordered_deal_changes_digest() -> None:
    """A reordered deal sequence is detectable through the normalized digest."""
    evidence = _evidence()
    evidence["deals"].append(  # type: ignore[union-attr]
        {
            "deal_id": "dl-2",
            "order_id": "ord-1",
            "position_id": "pos-1",
            "entry": "OUT",
            "reason": "FILL",
            "quantity": "0.1",
            "price": "1.1060",
            "executed_at": "2026-08-20T11:00:02+00:00",
        }
    )
    reordered = {
        **evidence,
        "deals": [evidence["deals"][1], evidence["deals"][0]],  # type: ignore[index]
    }
    first = normalize_parity_evidence(evidence, _ENVELOPE)
    second = normalize_parity_evidence(reordered, _ENVELOPE)
    assert first["canonical_digest"] != second["canonical_digest"]


def test_missing_deal_changes_digest() -> None:
    """A missing deal is detectable through the normalized digest."""
    full = normalize_parity_evidence(_evidence(), _ENVELOPE)
    evidence = _evidence()
    evidence["deals"] = ()  # type: ignore[assignment]
    partial = normalize_parity_evidence(evidence, _ENVELOPE)
    assert full["canonical_digest"] != partial["canonical_digest"]


def test_ambiguous_same_timestamp_events_form_explicit_group() -> None:
    """FR-SIM-239: identical timestamps form explicit ambiguous groups."""
    evidence = _evidence()
    evidence["events"][1]["occurred_at"] = "2026-08-20T11:00:00+00:00"  # type: ignore[index]
    envelope_model = load_parity_envelope("v1")
    normalized = normalize_parsed_evidence(evidence, envelope_model)
    # Encounter order: ord-1->a1, co-1->a2, rc-1->a3, in-1->a4, po-1->a5,
    # dl-1->a6, pos-1->a7, then events ev-1->a8 and ev-2->a9.
    assert normalized.ambiguous_time_groups == (("a8", "a9"),)
    ordering = [event.event_id for event in normalized.events]
    assert ordering == ["a8", "a9"]


def test_economic_time_drift_changes_digest() -> None:
    """FR-SIM-239: economic timestamp drift is detectable."""
    drifted = _evidence()
    drifted["events"][1]["occurred_at"] = "2026-08-20T11:00:09+00:00"  # type: ignore[index]
    baseline = normalize_parity_evidence(_evidence(), _ENVELOPE)
    drifted_view = normalize_parity_evidence(drifted, _ENVELOPE)
    assert baseline["canonical_digest"] != drifted_view["canonical_digest"]


def test_unregistered_evidence_field_rejected() -> None:
    """FR-SIM-188: fields outside the schema are rejected, never ignored."""
    evidence = _evidence()
    evidence["surprise_field"] = "not-in-registry"
    with pytest.raises(SimulationError) as raised:
        normalize_parity_evidence(evidence, _ENVELOPE)
    assert raised.value.code == "SIM_INVALID_CONFIG"


def test_registered_ignored_timestamps_are_stripped() -> None:
    """FR-SIM-188: only envelope-registered fields are excluded."""
    evidence = _evidence()
    evidence["orders"][0]["provider_timestamp"] = (  # type: ignore[index]
        "2026-08-20T11:00:00+00:00"
    )
    envelope_model = load_parity_envelope("v1")
    normalized = normalize_parsed_evidence(evidence, envelope_model)
    assert normalized.orders[0].provider_timestamp is None


def test_naive_timestamp_rejected() -> None:
    """Naive timestamps fail closed during evidence validation."""
    evidence = _evidence()
    evidence["orders"][0]["placed_at"] = "2026-08-20T11:00:00"  # type: ignore[index]
    with pytest.raises(SimulationError):
        normalize_parity_evidence(evidence, _ENVELOPE)


def test_float_money_value_rejected() -> None:
    """Binary floats are forbidden in monetary evidence fields."""
    evidence = _evidence()
    evidence["orders"][0]["quantity"] = 0.1  # type: ignore[index]
    with pytest.raises(SimulationError):
        normalize_parity_evidence(evidence, _ENVELOPE)
