"""Unit tests for the Portfolio balanced double-entry ledger (``FEAT-PORT-09``).

Covers ``FR-PORT-049``..``FR-PORT-055`` and the four Trading Cockpit gaps
``TC-IMP-PORT-01`` (balanced postings), ``TC-IMP-PORT-02`` (exactly-once
ingestion), ``TC-IMP-PORT-03`` (settled/unsettled cash), and
``TC-IMP-PORT-15`` (snapshot rebuild). All money math is deterministic
``decimal.Decimal`` (NFR-PORT-007, QUANT gate).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.portfolio.ledger import (
    build_ledger_account,
    build_ledger_entry,
    build_posting_batch,
    build_reversal_batch,
    build_snapshot,
    cash_balance,
    create_ledger_service,
    detect_sequence_gap,
    event_identity,
    ingest_event,
    is_balanced,
    parse_ledger_account,
    parse_ledger_entry,
    parse_posting_batch,
    recompute_balances,
    validate_snapshot,
)
from app.utils import get_logger

logger = get_logger(__name__)

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _balanced_legs(
    *,
    amount: Decimal = Decimal(100),
    currency: str = "USD",
    posting_type: str = "deposit",
) -> tuple[dict[str, object], ...]:
    """Return a balanced two-leg deposit posting."""
    return (
        {
            "entry_id": "leg-debit",
            "account_id": "cash-usd",
            "side": "debit",
            "amount": amount,
            "currency": currency,
            "posting_type": posting_type,
        },
        {
            "entry_id": "leg-credit",
            "account_id": "equity",
            "side": "credit",
            "amount": amount,
            "currency": currency,
            "posting_type": posting_type,
        },
    )


def test_fr_port_049_balanced_postings_sum_to_zero_per_currency() -> None:
    """FR-PORT-049: every batch must balance to zero in every currency."""
    logger.info("Testing ledger balance invariant")
    legs = _balanced_legs()
    assert is_balanced(legs) is True


def test_unbalanced_posting_is_rejected() -> None:
    """An unbalanced batch must fail validation."""
    logger.info("Testing ledger unbalance rejection")
    legs = (
        {
            "entry_id": "leg-1",
            "account_id": "cash",
            "side": "debit",
            "amount": Decimal(100),
            "currency": "USD",
            "posting_type": "deposit",
        },
        {
            "entry_id": "leg-2",
            "account_id": "equity",
            "side": "credit",
            "amount": Decimal(90),
            "currency": "USD",
            "posting_type": "deposit",
        },
    )
    with pytest.raises(ValueError, match="balance to zero"):
        build_posting_batch(
            batch_id="batch-unbalanced",
            source_event_id="ev-1",
            source_sequence=1,
            entry_sequence=1,
            entries=legs,
            posted_at=NOW,
            canonical_hash="a" * 64,
            request_id="req-1",
            correlation_id="corr-1",
        )


def test_multi_currency_batch_balances_independently_per_currency() -> None:
    """A batch spanning currencies must balance each currency independently."""
    legs = (
        {
            "entry_id": "leg-1",
            "account_id": "cash-usd",
            "side": "debit",
            "amount": Decimal(100),
            "currency": "USD",
            "posting_type": "deposit",
        },
        {
            "entry_id": "leg-2",
            "account_id": "equity-usd",
            "side": "credit",
            "amount": Decimal(100),
            "currency": "USD",
            "posting_type": "deposit",
        },
        {
            "entry_id": "leg-3",
            "account_id": "cash-eur",
            "side": "debit",
            "amount": Decimal(50),
            "currency": "EUR",
            "posting_type": "deposit",
        },
        {
            "entry_id": "leg-4",
            "account_id": "equity-eur",
            "side": "credit",
            "amount": Decimal(50),
            "currency": "EUR",
            "posting_type": "deposit",
        },
    )
    batch = build_posting_batch(
        batch_id="batch-multi",
        source_event_id="ev-multi",
        source_sequence=1,
        entry_sequence=1,
        entries=legs,
        posted_at=NOW,
        canonical_hash="b" * 64,
        request_id="req-2",
        correlation_id="corr-2",
    )
    assert len(batch["entries"]) == 4


def test_fr_port_050_exactly_once_ingestion_is_idempotent_for_identical_material() -> (
    None
):
    """FR-PORT-050: a replayed event with identical material is a no-op."""
    logger.info("Testing ledger exactly-once idempotent replay")
    legs = _balanced_legs()
    key, first_batch = ingest_event(
        source_event_id="ev-once",
        source_sequence=1,
        entries=legs,
        posted_at=NOW,
        request_id="req-1",
        correlation_id="corr-1",
        existing_keys={},
        next_entry_sequence=1,
    )
    assert first_batch != {}
    replayed, second_batch = ingest_event(
        source_event_id="ev-once",
        source_sequence=1,
        entries=legs,
        posted_at=NOW,
        request_id="req-1",
        correlation_id="corr-1",
        existing_keys={
            key: pytest.importorskip("app.services.portfolio.ledger").material_hash(
                {
                    "entries": [
                        {
                            "account_id": "cash-usd",
                            "side": "debit",
                            "amount": "100",
                            "currency": "USD",
                            "posting_type": "deposit",
                        },
                        {
                            "account_id": "equity",
                            "side": "credit",
                            "amount": "100",
                            "currency": "USD",
                            "posting_type": "deposit",
                        },
                    ],
                    "reversal_of": None,
                }
            )
        },
        next_entry_sequence=2,
    )
    assert replayed == key
    assert second_batch == {}


def test_exactly_once_ingestion_rejects_conflicting_material() -> None:
    """A replayed event with different material must fail closed."""
    logger.info("Testing ledger exactly-once conflict rejection")
    legs = _balanced_legs()
    key = event_identity("ev-conflict", 1)
    with pytest.raises(ValueError, match="conflict"):
        ingest_event(
            source_event_id="ev-conflict",
            source_sequence=1,
            entries=legs,
            posted_at=NOW,
            request_id="req-1",
            correlation_id="corr-1",
            existing_keys={key: "0" * 64},
            next_entry_sequence=1,
        )


def test_sequence_gap_detection_surfaces_missing_sequence() -> None:
    """A gap in a source-event sequence is surfaced, not silently accepted."""
    logger.info("Testing ledger sequence gap detection")
    assert detect_sequence_gap([1, 2, 4]) == 3
    assert detect_sequence_gap([1, 2, 3]) is None
    assert detect_sequence_gap([]) is None


def test_fr_port_051_settled_and_unsettled_cash_split() -> None:
    """FR-PORT-051: cash balances split settled from accrued income/cost."""
    logger.info("Testing ledger settled/accrued cash split")
    legs = _balanced_legs(posting_type="dividend")
    balance = cash_balance(legs, "cash-usd", "USD")
    assert balance.settled == Decimal(100)
    assert balance.accrued_income == Decimal(100)


def test_accrued_cost_tracks_financing_and_fees() -> None:
    """Financing and fee postings accrue as costs on the cash account."""
    logger.info("Testing ledger accrued cost accumulation")
    legs = _balanced_legs(posting_type="fee")
    balance = cash_balance(legs, "cash-usd", "USD")
    # debit cash increases settled; the leg is a cost type
    assert balance.accrued_cost == Decimal(100)


def test_fr_port_052_reproducible_balance_rebuild() -> None:
    """FR-PORT-052: identical ordered entries reproduce identical balances."""
    logger.info("Testing ledger deterministic balance rebuild")
    legs = _balanced_legs()
    first = recompute_balances(legs)
    second = recompute_balances(legs)
    assert first == second
    assert first[("cash-usd", "USD")] == Decimal(100)
    assert first[("equity", "USD")] == Decimal(-100)


def test_fr_port_053_append_only_correction_is_a_reversal_batch() -> None:
    """FR-PORT-053: corrections are reversal batches, never edits."""
    logger.info("Testing ledger append-only reversal correction")
    legs = _balanced_legs()
    original = build_posting_batch(
        batch_id="batch-original",
        source_event_id="ev-original",
        source_sequence=1,
        entry_sequence=1,
        entries=legs,
        posted_at=NOW,
        canonical_hash="c" * 64,
        request_id="req-1",
        correlation_id="corr-1",
    )
    reversal = build_reversal_batch(
        original=original,
        batch_id="batch-reversal",
        source_event_id="ev-reversal",
        source_sequence=2,
        entry_sequence=2,
        posted_at=NOW + timedelta(days=1),
        request_id="req-2",
        correlation_id="corr-2",
    )
    assert reversal["reversal_of"] == "batch-original"
    assert reversal["entries"][0]["side"] == "credit"
    assert reversal["entries"][1]["side"] == "debit"
    assert reversal["entries"][0]["posting_type"] == "correction"


def test_fr_port_054_snapshot_accelerator_validates_against_rebuild() -> None:
    """FR-PORT-054: a snapshot is an accelerator that must match the rebuild."""
    logger.info("Testing ledger snapshot rebuild validation")
    legs = _balanced_legs()
    snapshot = build_snapshot(
        snapshot_id="snap-1",
        entries=legs,
        entry_range_start=1,
        entry_range_end=2,
    )
    assert validate_snapshot(snapshot, legs) is True


def test_snapshot_disagreement_with_rebuild_is_detected() -> None:
    """A snapshot that disagrees with a rebuild is flagged stale."""
    logger.info("Testing ledger snapshot staleness detection")
    legs = _balanced_legs()
    snapshot = build_snapshot(
        snapshot_id="snap-2",
        entries=legs,
        entry_range_start=1,
        entry_range_end=2,
    )
    altered_legs = _balanced_legs(amount=Decimal(200))
    assert validate_snapshot(snapshot, altered_legs) is False


def test_fr_port_055_deterministic_output_for_identical_inputs() -> None:
    """FR-PORT-055: identical inputs produce identical outputs (QUANT gate)."""
    logger.info("Testing ledger determinism")
    legs = _balanced_legs()
    batch_a = build_posting_batch(
        batch_id="batch-det",
        source_event_id="ev-det",
        source_sequence=1,
        entry_sequence=1,
        entries=legs,
        posted_at=NOW,
        canonical_hash="d" * 64,
        request_id="req-1",
        correlation_id="corr-1",
    )
    batch_b = build_posting_batch(
        batch_id="batch-det",
        source_event_id="ev-det",
        source_sequence=1,
        entry_sequence=1,
        entries=legs,
        posted_at=NOW,
        canonical_hash="d" * 64,
        request_id="req-1",
        correlation_id="corr-1",
    )
    assert batch_a == batch_b


def test_ledger_entry_build_parse_roundtrip() -> None:
    """The LedgerEntry build/parse pair round-trips a JSON-safe mapping."""
    mapping = build_ledger_entry(
        entry_id="leg-1",
        account_id="cash-usd",
        side="debit",
        amount=Decimal(100),
        currency="USD",
        posting_type="deposit",
    )
    assert mapping["schema_id"] == "portfolio.ledger_entry.v1"
    parsed = parse_ledger_entry(mapping)
    assert parsed == mapping


def test_ledger_entry_rejects_negative_amount() -> None:
    """A negative leg magnitude is rejected."""
    with pytest.raises(ValueError, match="negative"):
        build_ledger_entry(
            entry_id="leg-neg",
            account_id="cash",
            side="debit",
            amount=Decimal(-1),
            currency="USD",
            posting_type="deposit",
        )


def test_ledger_entry_rejects_unknown_posting_type() -> None:
    """An unknown posting type is rejected."""
    with pytest.raises(ValueError, match="posting_type"):
        build_ledger_entry(
            entry_id="leg-bad",
            account_id="cash",
            side="debit",
            amount=Decimal(1),
            currency="USD",
            posting_type="money_laundering",  # type: ignore[arg-type]
        )


def test_posting_batch_parse_roundtrip() -> None:
    """The PostingBatch build/parse pair round-trips a JSON-safe mapping."""
    legs = _balanced_legs()
    mapping = build_posting_batch(
        batch_id="batch-rt",
        source_event_id="ev-rt",
        source_sequence=1,
        entry_sequence=1,
        entries=legs,
        posted_at=NOW,
        canonical_hash="e" * 64,
        request_id="req-rt",
        correlation_id="corr-rt",
    )
    parsed = parse_posting_batch(mapping)
    assert parsed == mapping


def test_ledger_account_build_parse_roundtrip() -> None:
    """The LedgerAccount build/parse pair round-trips a JSON-safe mapping."""
    mapping = build_ledger_account(
        account_id="cash-usd",
        portfolio_id="portfolio-1",
        currency="USD",
        normal_balance="debit",
        category="asset",
        registered_at=NOW,
        request_id="req-acc",
        correlation_id="corr-acc",
    )
    assert mapping["schema_id"] == "portfolio.ledger_account.v1"
    parsed = parse_ledger_account(mapping)
    assert parsed == mapping


def test_ledger_account_rejects_unknown_category() -> None:
    """An unknown account category is rejected."""
    with pytest.raises(ValueError, match="category"):
        build_ledger_account(
            account_id="cash",
            portfolio_id="portfolio-1",
            currency="USD",
            normal_balance="debit",
            category="off_balance",  # type: ignore[arg-type]
            registered_at=NOW,
            request_id="req-acc",
            correlation_id="corr-acc",
        )


def test_ledger_service_coordinates_post_and_balance() -> None:
    """The LedgerService emits a balanced batch and computes balances."""
    logger.info("Testing ledger service coordination")
    service = create_ledger_service()
    legs = _balanced_legs()
    batch = service.post_entries(
        source_event_id="ev-svc",
        source_sequence=1,
        entries=legs,
        posted_at=NOW,
        request_id="req-svc",
        correlation_id="corr-svc",
        recorded_keys={},
        next_entry_sequence=1,
    )
    assert batch["schema_id"] == "portfolio.posting_batch.v1"
    balances = service.all_balances(legs)
    assert balances[("cash-usd", "USD")] == Decimal(100)


def test_ledger_service_rejects_unbalanced_input() -> None:
    """The service fails closed on unbalanced legs."""
    service = create_ledger_service()
    legs = (
        {
            "entry_id": "leg-1",
            "account_id": "cash",
            "side": "debit",
            "amount": Decimal(100),
            "currency": "USD",
            "posting_type": "deposit",
        },
        {
            "entry_id": "leg-2",
            "account_id": "equity",
            "side": "credit",
            "amount": Decimal(99),
            "currency": "USD",
            "posting_type": "deposit",
        },
    )
    with pytest.raises(ValueError, match="balance"):
        service.post_entries(
            source_event_id="ev-bad",
            source_sequence=1,
            entries=legs,
            posted_at=NOW,
            request_id="req-bad",
            correlation_id="corr-bad",
            recorded_keys={},
            next_entry_sequence=1,
        )


def test_ledger_service_snapshot_verification() -> None:
    """The service builds and verifies a rebuild-validated snapshot."""
    service = create_ledger_service()
    legs = _balanced_legs()
    snapshot = service.snapshot(
        snapshot_id="snap-svc",
        entries=legs,
        entry_range_start=1,
        entry_range_end=2,
    )
    assert service.verify_snapshot(snapshot, legs) is True


def test_posting_batch_requires_at_least_two_entries() -> None:
    """A single-leg batch is rejected (no balanced double-entry)."""
    legs = (
        {
            "entry_id": "leg-1",
            "account_id": "cash",
            "side": "debit",
            "amount": Decimal(100),
            "currency": "USD",
            "posting_type": "deposit",
        },
    )
    with pytest.raises(ValueError, match="at least two"):
        build_posting_batch(
            batch_id="batch-single",
            source_event_id="ev-single",
            source_sequence=1,
            entry_sequence=1,
            entries=legs,
            posted_at=NOW,
            canonical_hash="f" * 64,
            request_id="req-1",
            correlation_id="corr-1",
        )


def test_all_sixteen_posting_types_are_accepted() -> None:
    """Every posting type in the TC-IMP-PORT-01 catalogue is accepted."""
    accepted = {
        "deposit",
        "withdrawal",
        "fill",
        "commission",
        "fee",
        "spread",
        "financing",
        "funding",
        "borrow",
        "dividend",
        "fx_translation",
        "mark_to_market",
        "settlement",
        "corporate_action",
        "liquidation",
        "correction",
    }
    for posting_type in accepted:
        mapping = build_ledger_entry(
            entry_id=f"leg-{posting_type}",
            account_id="cash",
            side="debit",
            amount=Decimal(1),
            currency="USD",
            posting_type=posting_type,
        )
        assert mapping["posting_type"] == posting_type


def test_cash_balance_is_reproducible_across_runs() -> None:
    """Two cash-balance computations on the same legs are identical."""
    legs = _balanced_legs()
    first = cash_balance(legs, "cash-usd", "USD")
    second = cash_balance(legs, "cash-usd", "USD")
    assert first == second


def test_event_identity_is_deterministic() -> None:
    """The exactly-once key is deterministic for the same event/sequence."""
    assert event_identity("ev-1", 1) == event_identity("ev-1", 1)
    assert event_identity("ev-1", 1) != event_identity("ev-1", 2)
    assert event_identity("ev-1", 1) != event_identity("ev-2", 1)


def _entry_data(**overrides: object) -> dict[str, object]:
    """Return complete ledger entry constructor data."""
    data: dict[str, object] = {
        "entry_id": "leg-1",
        "account_id": "cash-usd",
        "side": "debit",
        "amount": Decimal(100),
        "currency": "USD",
        "posting_type": "deposit",
    }
    data.update(overrides)
    return data


def test_ledger_entry_serialization_is_json_safe() -> None:
    """A built entry is JSON-safe (D-1 transport contract)."""
    import json

    mapping = build_ledger_entry(**_entry_data())
    serialized = json.dumps(mapping)
    assert json.loads(serialized) == mapping


def test_total_entries_returns_per_currency_totals() -> None:
    """``total_entries`` returns debit-minus-credit totals per currency."""
    from app.services.portfolio.ledger.postings import total_entries

    legs = _balanced_legs()
    totals = total_entries(legs)
    assert totals["USD"] == Decimal(0)


def test_total_entries_rejects_missing_currency() -> None:
    """A leg missing its currency is rejected."""
    from app.services.portfolio.ledger.postings import total_entries

    legs = (
        {
            "entry_id": "leg-1",
            "account_id": "cash",
            "side": "debit",
            "amount": Decimal(1),
            "posting_type": "deposit",
        },
    )
    with pytest.raises(ValueError, match="currency"):
        total_entries(legs)


def test_signed_amount_rejects_unknown_side() -> None:
    """An unknown posting side is rejected by the signed-amount helper."""
    from app.services.portfolio.ledger.postings import _signed_amount

    with pytest.raises(ValueError, match="unknown posting side"):
        _signed_amount({"side": "maybe", "amount": Decimal(1)})


def test_account_balance_returns_per_currency_balance() -> None:
    """``account_balance`` returns the signed balance for one account."""
    from app.services.portfolio.ledger.postings import account_balance

    legs = _balanced_legs()
    balance = account_balance(legs, "cash-usd")
    assert balance["USD"] == Decimal(100)
    # Account not present returns empty.
    assert account_balance(legs, "nonexistent") == {}


def test_balance_from_models_rebuilds_from_typed_legs() -> None:
    """``balance_from_models`` rebuilds balances from typed leg models."""
    from app.services.portfolio.ledger.postings import (
        balance_from_models,
        batch_from_mapping,
    )

    legs = _balanced_legs()
    batch_mapping = build_posting_batch(
        batch_id="batch-models",
        source_event_id="ev-models",
        source_sequence=1,
        entry_sequence=1,
        entries=legs,
        posted_at=NOW,
        canonical_hash="g" * 64,
        request_id="req-models",
        correlation_id="corr-models",
    )
    batch = batch_from_mapping(batch_mapping)
    balances = balance_from_models(batch.entries)
    assert balances[("cash-usd", "USD")] == Decimal(100)


def test_normalize_entry_sequence_returns_next_index() -> None:
    """``normalize_entry_sequence`` returns the next monotonically increasing index."""
    from app.services.portfolio.ledger.postings import normalize_entry_sequence

    assert normalize_entry_sequence([]) == 1
    assert normalize_entry_sequence([{"entry_sequence": 5}]) == 6
    assert normalize_entry_sequence([{"entry_sequence": 3}, {"entry_sequence": 7}]) == 8


def test_is_balanced_returns_false_for_unbalanced() -> None:
    """``is_balanced`` returns False for unbalanced legs."""
    legs = (
        {
            "entry_id": "leg-1",
            "account_id": "cash",
            "side": "debit",
            "amount": Decimal(100),
            "currency": "USD",
            "posting_type": "deposit",
        },
        {
            "entry_id": "leg-2",
            "account_id": "equity",
            "side": "credit",
            "amount": Decimal(50),
            "currency": "USD",
            "posting_type": "deposit",
        },
    )
    assert is_balanced(legs) is False
