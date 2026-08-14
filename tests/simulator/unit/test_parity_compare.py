"""Unit tests for the parity comparator invariants and budgets."""

from decimal import Decimal

from app.services.simulator import (
    compare_parity_evidence,
    get_parity_envelope,
)
from app.services.simulator.parity.compare import _Comparator
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
                "entry": "IN",
                "reason": "FILL",
                "quantity": "0.1",
                "price": "1.1050",
                "executed_at": "2026-08-20T11:00:01+00:00",
            }
        ],
        "positions": [],
        "receipts": [],
        "events": [],
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


def _compare(right: dict[str, object]) -> dict[str, object]:
    return dict(compare_parity_evidence(_evidence(), right, _ENVELOPE))


def test_numeric_tolerance_exceeded_fails_invariant() -> None:
    """FR-SIM-191: an economic numeric drift fails its bounded invariant."""
    drifted = _evidence()
    ledger = drifted["ledger"]  # type: ignore[index]
    ledger["final_balance"] = "10006"
    result = _compare(drifted)
    assert result["passed"] is False
    failed = [f for f in result["failures"] if "account.final_balance" in f]
    assert failed


def test_aggregate_budget_exhaustion_detected() -> None:
    """Many individually tolerated differences cannot accumulate silently."""
    drifted = _evidence()
    ledger = drifted["ledger"]  # type: ignore[index]
    ledger["final_balance"] = "10006"
    ledger["final_equity"] = "10006"
    result = _compare(drifted)
    assert Decimal(str(result["aggregate_economic_error"])) == Decimal(2)
    assert any(
        f.startswith("aggregate.economic_error_budget") for f in result["failures"]
    )


def test_initial_state_mutation_invalidates_certificate() -> None:
    """FR-SIM-190: a changed initial-authority hash invalidates the certificate."""
    mutated = _evidence()
    mutated["initial_authority_state"] = {  # type: ignore[index]
        "state_hash": "a" * 64,
        "exclusive_account": True,
        "foreign_activity_event_count": 0,
    }
    result = _compare(mutated)
    assert result["passed"] is False
    assert result["certificate_invalidated"] is True
    assert any("certificate.initial_authority_state" in f for f in result["failures"])


def test_certificate_expiry_invalidates_result() -> None:
    """FR-SIM-237: an evaluation outside the validity window invalidates."""
    expired = _evidence()
    expired["evaluation_time"] = "2027-12-01T00:00:00+00:00"
    result = _compare(expired)
    assert result["certificate_invalidated"] is True
    assert result["passed"] is False
    assert any("certificate.validity" in f for f in result["failures"])


def test_ledger_conservation_violation_fails() -> None:
    """FR-SIM-192: a broken signed conservation equation fails comparison."""
    broken = _evidence()
    ledger = broken["ledger"]  # type: ignore[index]
    ledger["final_balance"] = "10050"
    result = _compare(broken)
    assert result["passed"] is False
    assert any("ledger.conservation" in f for f in result["failures"])


def test_missing_foreign_activity_blocks_comparison() -> None:
    """Non-exclusive evidence without replay events cannot certify."""
    incomplete = _evidence()
    incomplete["initial_authority_state"] = {  # type: ignore[index]
        "state_hash": "f" * 64,
        "exclusive_account": False,
        "foreign_activity_event_count": 2,
    }
    result = _compare(incomplete)
    assert result["passed"] is False
    assert any("certificate.foreign_activity" in f for f in result["failures"])


def test_distributional_insufficient_coverage_fails_closed() -> None:
    """FR-SIM-187: below-minimum sample coverage never passes a distribution."""
    base = load_parity_envelope("v1")
    calibrated = base.model_copy(
        update={
            "invariants": tuple(
                (
                    spec.model_copy(
                        update={
                            "tolerance": Decimal(10),
                            "awaiting_calibration_evidence": False,
                        }
                    )
                    if spec.invariant_id == "latency.submission_to_ack"
                    else spec
                )
                for spec in base.invariants
            )
        }
    )
    left = normalize_parsed_evidence(_evidence(), calibrated)
    right = normalize_parsed_evidence(_evidence(), calibrated)
    outcome = _Comparator(left, right, calibrated).run()
    latency = next(
        r
        for r in outcome.invariant_results
        if r.invariant_id == "latency.submission_to_ack"
    )
    assert latency.passed is False
    assert latency.detail is not None
    assert "sample coverage" in latency.detail


def test_awaiting_calibration_invariant_is_excluded_not_invented() -> None:
    """No threshold is invented before FEAT-SIM-17 publishes calibration."""
    left = normalize_parsed_evidence(_evidence(), load_parity_envelope("v1"))
    right = normalize_parsed_evidence(_evidence(), load_parity_envelope("v1"))
    outcome = _Comparator(left, right, load_parity_envelope("v1")).run()
    latency = next(
        r
        for r in outcome.invariant_results
        if r.invariant_id == "latency.submission_to_ack"
    )
    assert latency.passed is True
    assert latency.detail is not None
    assert latency.detail.startswith("not_certified")
