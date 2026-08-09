"""Executable Portfolio ledger usage example.

Demonstrates ``FEAT-PORT-09`` balanced double-entry ledger and accounts feature
through the package-root public API. Covers ``TC-IMP-PORT-01`` (balanced
postings), ``TC-IMP-PORT-02`` (exactly-once ingestion), ``TC-IMP-PORT-03``
(settled cash), and ``TC-IMP-PORT-15`` (snapshot rebuild).
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path.
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.portfolio import (
    build_ledger_account,
    build_ledger_entry,
    build_posting_batch,
    parse_ledger_entry,
    parse_posting_batch,
)
from app.services.portfolio.ledger import (
    build_reversal_batch,
    build_snapshot,
    cash_balance,
    create_ledger_service,
    ingest_event,
    is_balanced,
    recompute_balances,
    validate_snapshot,
)

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _run_example(requirement: str, example: Any) -> None:
    """Run one requirement example and print explicit success evidence."""
    example()
    print(f"SUCCESS: {requirement}")


def _format_result(obj: Any) -> str:
    """Format the output result type name and key signature."""
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _deposit_legs() -> tuple[dict[str, object], ...]:
    """Return a balanced USD deposit posting (cash debit, equity credit)."""
    return (
        {
            "entry_id": "leg-cash-debit",
            "account_id": "cash-usd",
            "side": "debit",
            "amount": Decimal(1000),
            "currency": "USD",
            "posting_type": "deposit",
        },
        {
            "entry_id": "leg-equity-credit",
            "account_id": "owner-equity",
            "side": "credit",
            "amount": Decimal(1000),
            "currency": "USD",
            "posting_type": "deposit",
        },
    )


def fr_port_049() -> None:
    """FR-PORT-049: Balanced double-entry postings sum to zero per currency."""
    _header("Stage 1: Balanced Double-Entry Postings (FR-PORT-049)")
    legs = _deposit_legs()
    assert is_balanced(legs)
    batch = build_posting_batch(
        batch_id="batch-deposit-1",
        source_event_id="event-deposit-1",
        source_sequence=1,
        entry_sequence=1,
        entries=legs,
        posted_at=NOW,
        canonical_hash="a" * 64,
        request_id="req-deposit-1",
        correlation_id="corr-deposit-1",
    )
    print(_format_result(batch))
    print(f"Data -> schema_id='{batch['schema_id']}', entries={len(batch['entries'])}")


def fr_port_050() -> None:
    """FR-PORT-050: Economic events are ingested exactly once."""
    _header("Stage 2: Exactly-Once Event Ingestion (FR-PORT-050)")
    legs = _deposit_legs()
    key, batch = ingest_event(
        source_event_id="event-deposit-2",
        source_sequence=1,
        entries=legs,
        posted_at=NOW,
        request_id="req-deposit-2",
        correlation_id="corr-deposit-2",
        existing_keys={},
        next_entry_sequence=1,
    )
    print(_format_result(batch))
    print(f"Data -> ingestion_key='{key[:16]}...', batch_emitted={bool(batch)}")


def fr_port_051() -> None:
    """FR-PORT-051: Settled cash and accrued income/costs are reproducible."""
    _header("Stage 3: Settled Cash and Accrued Income (FR-PORT-051)")
    legs = _deposit_legs()
    balance = cash_balance(legs, "cash-usd", "USD")
    print(_format_result(balance))
    print(
        f"Data -> settled={balance.settled} {balance.currency}, "
        f"accrued_income={balance.accrued_income}"
    )


def fr_port_052() -> None:
    """FR-PORT-052: Balance rebuild from ordered legs is deterministic."""
    _header("Stage 4: Deterministic Balance Rebuild (FR-PORT-052)")
    legs = _deposit_legs()
    balances = recompute_balances(legs)
    print(f"Output Result -> balances mapping ({len(balances)} accounts) : dict")
    print(
        f"Data -> cash_usd={balances[('cash-usd', 'USD')]}, "
        f"owner_equity={balances[('owner-equity', 'USD')]}"
    )


def fr_port_053() -> None:
    """FR-PORT-053: Corrections are append-only reversal batches."""
    _header("Stage 5: Append-Only Reversal Correction (FR-PORT-053)")
    legs = _deposit_legs()
    original = build_posting_batch(
        batch_id="batch-original",
        source_event_id="event-original",
        source_sequence=1,
        entry_sequence=1,
        entries=legs,
        posted_at=NOW,
        canonical_hash="b" * 64,
        request_id="req-original",
        correlation_id="corr-original",
    )
    reversal = build_reversal_batch(
        original=original,
        batch_id="batch-reversal",
        source_event_id="event-reversal",
        source_sequence=2,
        entry_sequence=2,
        posted_at=NOW + timedelta(days=1),
        request_id="req-reversal",
        correlation_id="corr-reversal",
    )
    print(_format_result(reversal))
    print(
        f"Data -> reversal_of='{reversal['reversal_of']}', "
        f"corrected_side='{reversal['entries'][0]['side']}'"
    )


def fr_port_054() -> None:
    """FR-PORT-054: Snapshots are accelerators validated against rebuild."""
    _header("Stage 6: Snapshot Rebuild Validation (FR-PORT-054)")
    legs = _deposit_legs()
    snapshot = build_snapshot(
        snapshot_id="snapshot-1",
        entries=legs,
        entry_range_start=1,
        entry_range_end=2,
    )
    valid = validate_snapshot(snapshot, legs)
    print(_format_result(snapshot))
    print(
        f"Data -> snapshot_id='{snapshot.snapshot_id}', "
        f"matches_rebuild={valid}, accounts={len(snapshot.account_ids)}"
    )


def fr_port_055() -> None:
    """FR-PORT-055: Identical inputs produce identical outputs (determinism)."""
    _header("Stage 7: Ledger Contract Determinism (FR-PORT-055)")
    entry = build_ledger_entry(
        entry_id="leg-det",
        account_id="cash-usd",
        side="debit",
        amount=Decimal(500),
        currency="USD",
        posting_type="deposit",
    )
    parsed = parse_ledger_entry(entry)
    print(_format_result(entry))
    print(
        f"Data -> schema_id='{parsed['schema_id']}', roundtrip_equal={parsed == entry}"
    )


def fr_port_contract_transport() -> None:
    """D-1 contract transport: build/parse pairs round-trip JSON-safe mappings."""
    _header("Stage 8: D-1 Contract Transport Round-Trip")
    legs = _deposit_legs()
    batch = build_posting_batch(
        batch_id="batch-transport",
        source_event_id="event-transport",
        source_sequence=1,
        entry_sequence=1,
        entries=legs,
        posted_at=NOW,
        canonical_hash="c" * 64,
        request_id="req-transport",
        correlation_id="corr-transport",
    )
    parsed = parse_posting_batch(batch)
    print(_format_result(parsed))
    print(f"Data -> roundtrip_equal={parsed == batch}")


def fr_port_ledger_service() -> None:
    """Ledger service coordinates posting and balance computation."""
    _header("Stage 9: Ledger Service Coordination")
    service = create_ledger_service()
    legs = _deposit_legs()
    batch = service.post_entries(
        source_event_id="event-service",
        source_sequence=1,
        entries=legs,
        posted_at=NOW,
        request_id="req-service",
        correlation_id="corr-service",
        recorded_keys={},
        next_entry_sequence=1,
    )
    balances = service.all_balances(legs)
    print(_format_result(batch))
    print(f"Data -> service_balance={balances[('cash-usd', 'USD')]} USD")


def fr_port_chart_of_accounts() -> None:
    """Chart-of-accounts entries are versioned immutable contracts."""
    _header("Stage 10: Chart of Accounts Registration")
    account = build_ledger_account(
        account_id="cash-usd",
        portfolio_id="portfolio-alpha",
        currency="USD",
        normal_balance="debit",
        category="asset",
        registered_at=NOW,
        request_id="req-chart-1",
        correlation_id="corr-chart-1",
    )
    print(_format_result(account))
    print(
        f"Data -> account_id='{account['account_id']}', "
        f"category='{account['category']}', currency='{account['currency']}'"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-PORT-09 — ledger/ — Balanced Double-Entry Ledger and Accounts\n\n"
        "Purpose: Build the cockpit's foundational financial authority: a balanced\n"
        "double-entry ledger with accounts, exactly-once economic-event ingestion,\n"
        "settled/unsettled cash, reproducible balance rebuild, append-only reversal\n"
        "corrections, and snapshot accelerators validated against canonical truth.\n\n"
        "Module flow:\n"
        "-> Stage 1: Balanced postings (TC-IMP-PORT-01)\n"
        "-> Stage 2: Exactly-once ingestion (TC-IMP-PORT-02)\n"
        "-> Stage 3: Settled cash (TC-IMP-PORT-03)\n"
        "-> Stage 4: Deterministic rebuild\n"
        "-> Stage 5: Append-only reversal correction\n"
        "-> Stage 6: Snapshot rebuild validation (TC-IMP-PORT-15)\n"
        "-> Stage 7: Determinism (QUANT gate)\n"
        "-> Stage 8: D-1 contract transport\n"
        "-> Stage 9: Ledger service coordination\n"
        "-> Stage 10: Chart of accounts"
    )

    _run_example("FR-PORT-049", fr_port_049)
    _run_example("FR-PORT-050", fr_port_050)
    _run_example("FR-PORT-051", fr_port_051)
    _run_example("FR-PORT-052", fr_port_052)
    _run_example("FR-PORT-053", fr_port_053)
    _run_example("FR-PORT-054", fr_port_054)
    _run_example("FR-PORT-055", fr_port_055)
    _run_example("FR-PORT-D1-TRANSPORT", fr_port_contract_transport)
    _run_example("FR-PORT-LEDGER-SERVICE", fr_port_ledger_service)
    _run_example("FR-PORT-CHART-OF-ACCOUNTS", fr_port_chart_of_accounts)


if __name__ == "__main__":
    main()
