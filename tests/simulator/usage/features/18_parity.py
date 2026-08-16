"""Standalone usage for FEAT-SIM-18 parity envelope and comparator."""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import (
    compare_parity_evidence,
    get_parity_envelope,
    get_parity_maturity_ladder,
    normalize_parity_evidence,
)


def _evidence(certificate_target: str = "demo") -> dict[str, object]:
    """Build one bounded secret-free demo parity evidence mapping."""
    return {
        "certificate_target": certificate_target,
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
                "route": "demo",
                "route_specific": True,
                "route_policy": "validate_adapter_capability_exact_match",
            },
        ),
        "orders": (
            {
                "order_id": "ord-usage",
                "client_order_id": "co-usage",
                "symbol": "EURUSD",
                "side": "BUY",
                "order_type": "MARKET",
                "state": "FILLED",
                "quantity": "0.1",
                "filled": "0.1",
                "placed_at": "2026-08-20T11:00:00+00:00",
            },
        ),
        "deals": (
            {
                "deal_id": "dl-usage",
                "order_id": "ord-usage",
                "position_id": "pos-usage",
                "entry": "IN",
                "reason": "FILL",
                "quantity": "0.1",
                "price": "1.1050",
                "executed_at": "2026-08-20T11:00:01+00:00",
            },
        ),
        "positions": (
            {
                "position_id": "pos-usage",
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
                "receipt_id": "rc-usage",
                "intent_id": "in-usage",
                "client_order_id": "co-usage",
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
                "provider_order_id": "po-usage",
                "provider_deal_ids": ["dl-usage"],
            },
        ),
        "events": (
            {
                "event_id": "ev-usage-1",
                "event_type": "order_accepted",
                "occurred_at": "2026-08-20T11:00:00+00:00",
                "source_sequence": 0,
            },
            {
                "event_id": "ev-usage-2",
                "event_type": "order_outcome",
                "occurred_at": "2026-08-20T11:00:01+00:00",
                "causes": ["ev-usage-1"],
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
                    "posting_id": "p-usage",
                    "kind": "realized_profit",
                    "amount": "5",
                    "occurred_at": "2026-08-20T11:00:01+00:00",
                    "source_sequence": 0,
                },
            ),
        },
    }


def _renamed_right() -> dict[str, object]:
    """Build the paired provider-side evidence with different raw identifiers."""
    right: dict[str, Any] = dict(_evidence())
    right["orders"] = (
        {
            **_evidence()["orders"][0],  # type: ignore[index]
            "order_id": "MT-ORD-1",
            "client_order_id": "MT-CO-1",
        },
    )
    right["deals"] = (
        {
            **_evidence()["deals"][0],  # type: ignore[index]
            "deal_id": "MT-DEAL-1",
            "order_id": "MT-ORD-1",
            "position_id": "MT-POS-1",
        },
    )
    right["positions"] = (
        {
            **_evidence()["positions"][0],  # type: ignore[index]
            "position_id": "MT-POS-1",
        },
    )
    base_receipt = _evidence()["receipts"][0]  # type: ignore[index]
    right["receipts"] = (
        {
            **base_receipt,
            "receipt_id": "MT-RC-1",
            "intent_id": "MT-IN-1",
            "client_order_id": "MT-CO-1",
            "provider_order_id": "MT-PO-1",
            "provider_deal_ids": ["MT-DEAL-1"],
        },
    )
    base_events = _evidence()["events"]  # type: ignore[assignment]
    right["events"] = (
        {**base_events[0], "event_id": "MT-EV-1"},
        {**base_events[1], "event_id": "MT-EV-2", "causes": ["MT-EV-1"]},
    )
    base_posting = _evidence()["ledger"]["postings"][0]  # type: ignore[index]
    right["ledger"] = {
        **_evidence()["ledger"],  # type: ignore[index]
        "postings": ({**base_posting, "posting_id": "MT-P1"},),
    }
    return right


def fr_sim_187() -> None:
    """FR-SIM-187: Simulator shall define typed parity invariant groups with exact metric, unit, tolerance or statistical test, minimum coverage, and aggregation rule."""
    envelope = get_parity_envelope("v1")
    kinds = {item["kind"] for item in envelope["invariants"]}  # type: ignore[index]
    assert kinds == {"exact_structural", "bounded_numeric", "distributional"}
    print(f"SUCCESS: FR-SIM-187 invariant kinds published -> {sorted(kinds)}")


def fr_sim_188() -> None:
    """FR-SIM-188: Simulator shall own a versioned normalizer registry whose ignored fields are explicit and whose unknown fields fail closed."""
    envelope = get_parity_envelope("v1")
    view = normalize_parity_evidence(_evidence(), envelope)
    assert view["canonical_digest"]
    tainted = {**_evidence(), "unregistered_field": True}
    try:
        normalize_parity_evidence(tainted, envelope)
    except Exception as error:  # noqa: BLE001
        code = getattr(error, "code", "")
        assert code == "SIM_INVALID_CONFIG"
        print(f"SUCCESS: FR-SIM-188 unregistered field rejected -> {code}")
    else:
        raise AssertionError("unregistered field must fail closed")


def fr_sim_189() -> None:
    """FR-SIM-189: Simulator shall prove cold re-execution from fresh stores and artifact roots is identical through canonical normalization digests."""
    envelope = get_parity_envelope("v1")
    first = normalize_parity_evidence(_evidence(), envelope)
    second = normalize_parity_evidence(_evidence(), envelope)
    assert first["canonical_digest"] == second["canonical_digest"]
    print("SUCCESS: FR-SIM-189 cold normalization digests identical")


def fr_sim_190() -> None:
    """FR-SIM-190: Simulator shall bind execution and complete initial-authority-state identity into run identity for certification."""
    envelope = get_parity_envelope("v1")
    mutated = _evidence()
    mutated["initial_authority_state"] = {  # type: ignore[index]
        "state_hash": "a" * 64,
        "exclusive_account": True,
        "foreign_activity_event_count": 0,
    }
    result = compare_parity_evidence(mutated, _renamed_right(), envelope)
    assert result["certificate_invalidated"] is True
    print("SUCCESS: FR-SIM-190 initial-state mutation invalidates certificate")


def fr_sim_191() -> None:
    """FR-SIM-191: Simulator shall reject approximation, fallback, staleness, or uncovered behavior for canonical parity execution."""
    envelope = get_parity_envelope("v1")
    drifted = _evidence()
    ledger = drifted["ledger"]  # type: ignore[index]
    ledger["final_balance"] = "10006"
    result = compare_parity_evidence(drifted, _renamed_right(), envelope)
    assert result["passed"] is False
    print("SUCCESS: FR-SIM-191 economic drift rejected; no fallback applied")


def fr_sim_192() -> None:
    """FR-SIM-192: Simulator shall enforce signed ledger conservation after every comparison."""
    envelope = get_parity_envelope("v1")
    broken = _evidence()
    ledger = broken["ledger"]  # type: ignore[index]
    ledger["final_balance"] = "10050"
    result = compare_parity_evidence(broken, _renamed_right(), envelope)
    assert any("ledger.conservation" in f for f in result["failures"])  # type: ignore[index]
    print("SUCCESS: FR-SIM-192 conservation violation reported")


def fr_sim_193() -> None:
    """FR-SIM-193: Simulator shall publish the L1 through L5-Demo/L5-Live maturity ladder with distinct certificates."""
    ladder = get_parity_maturity_ladder()
    rungs = [rung["rung"] for rung in ladder]
    assert rungs == ["L1", "L2", "L3", "L4", "L5-Demo", "L5-Live"]
    print(f"SUCCESS: FR-SIM-193 ladder published -> {rungs}")


def fr_sim_236() -> None:
    """FR-SIM-236: Simulator shall publish the versioned envelope matrix with evidence class, certificate scope, thresholds, and validity interval."""
    envelope = get_parity_envelope("v1")
    assert envelope["certificate_scope"]["certificate_target"] == "demo"
    assert envelope["validity"]["valid_through"]
    print("SUCCESS: FR-SIM-236 envelope v1 matrix published")


def fr_sim_237() -> None:
    """FR-SIM-237: Simulator shall reject work outside the envelope and invalidate stale certificates."""
    envelope = get_parity_envelope("v1")
    relabelled = _evidence(certificate_target="live")
    try:
        compare_parity_evidence(relabelled, _renamed_right(), envelope)
    except Exception as error:  # noqa: BLE001
        code = getattr(error, "code", "")
        assert code == "SIM_INVALID_CONFIG"
        print(f"SUCCESS: FR-SIM-237 scope violation rejected -> {code}")
    else:
        raise AssertionError("demo evidence must not claim live scope")
    expired = _evidence()
    expired["evaluation_time"] = "2027-12-01T00:00:00+00:00"
    result = compare_parity_evidence(expired, _renamed_right(), envelope)
    assert result["certificate_invalidated"] is True


def fr_sim_238() -> None:
    """FR-SIM-238: Simulator shall preserve identifier cardinality, foreign keys, and causal edges under alpha-renaming normalization."""
    envelope = get_parity_envelope("v1")
    left = normalize_parity_evidence(_evidence(), envelope)
    right = normalize_parity_evidence(_renamed_right(), envelope)
    assert left["canonical_digest"] == right["canonical_digest"]
    assert left["identifier_map"] != right["identifier_map"]
    print("SUCCESS: FR-SIM-238 alpha-equivalent graphs normalize identically")


def fr_sim_239() -> None:
    """FR-SIM-239: Simulator shall preserve economic time, evidenced partial order, and duration semantics under normalization."""
    envelope = get_parity_envelope("v1")
    drifted = _evidence()
    drifted["events"][1]["occurred_at"] = "2026-08-20T11:00:09+00:00"  # type: ignore[index]
    baseline = normalize_parity_evidence(_evidence(), envelope)
    drifted_view = normalize_parity_evidence(drifted, envelope)
    assert baseline["canonical_digest"] != drifted_view["canonical_digest"]
    print("SUCCESS: FR-SIM-239 economic-time drift detected")


def main() -> None:
    """Run every FEAT-SIM-18 usage function."""
    print("FEATURE: FEAT-SIM-18 — Parity Comparison")
    fr_sim_187()
    fr_sim_188()
    fr_sim_189()
    fr_sim_190()
    fr_sim_191()
    fr_sim_192()
    fr_sim_193()
    fr_sim_236()
    fr_sim_237()
    fr_sim_238()
    fr_sim_239()


if __name__ == "__main__":
    main()
