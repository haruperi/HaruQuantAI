"""Fast contract tests for FEAT-DATA-18 catalog operations."""

from decimal import Decimal
from pathlib import Path

import pytest
from app.services.data import (
    get_catalog_evidence,
    get_catalog_table_lifecycles,
    reconcile_data_catalog,
    sync_catalog_reference,
)
from app.services.data.artifact_catalog import operations
from app.services.data.contracts import DataError
from app.utils import generate_id

_REQUEST_ID = generate_id("req")


class _Rows:
    """Minimal persistence result used to isolate database I/O."""

    rows = ({"value": 1},)


def _rows(*_args: object, **_kwargs: object) -> _Rows:
    """Return isolated persistence evidence for any read signature."""
    return _Rows()


def test_catalog_evidence_combines_all_bounded_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The public evidence read delegates to every catalog evidence source."""
    for name in (
        "read_catalog_reference_records",
        "read_catalog_files_for_range",
        "read_catalog_unverified_count",
        "read_catalog_coverage",
        "read_catalog_event_records",
    ):
        monkeypatch.setattr(operations, name, _rows)

    evidence = get_catalog_evidence(
        dataset_id="dataset",
        symbol_id="symbol",
        provider_id="provider",
        range_start_utc=1,
        range_end_utc=2,
        request_id=_REQUEST_ID,
    )

    assert set(evidence) == {
        "reference",
        "artifacts",
        "integrity",
        "coverage",
        "events",
    }


@pytest.mark.parametrize(
    ("start", "end", "limit"),
    [(2, 1, 1), (1, 2, 0), (1, 2, 1001)],
)
def test_catalog_evidence_rejects_invalid_bounds(
    start: int, end: int, limit: int
) -> None:
    """Invalid ranges and limits fail closed before persistence access."""
    with pytest.raises(DataError):
        get_catalog_evidence(
            dataset_id="dataset",
            symbol_id="symbol",
            provider_id="provider",
            range_start_utc=start,
            range_end_utc=end,
            request_id=_REQUEST_ID,
            limit=limit,
        )


def test_empty_catalog_reconciliation_is_deterministic(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An empty authoritative artifact root reconciles to explicit zero counts."""
    monkeypatch.setattr(operations, "resolve_data_root", lambda _request_id: tmp_path)

    assert reconcile_data_catalog(request_id=_REQUEST_ID) == {
        "scanned": 0,
        "indexed": 0,
    }


def test_catalog_reconciliation_rejects_invalid_limit() -> None:
    """The rebuild scan cannot be unbounded or disabled ambiguously."""
    with pytest.raises(DataError):
        reconcile_data_catalog(request_id=_REQUEST_ID, max_files=0)


def test_catalog_lifecycle_inventory_and_reference_validation() -> None:
    """Lifecycle evidence is complete and blank identities fail closed."""
    assert len(get_catalog_table_lifecycles()) == 23
    with pytest.raises(DataError):
        sync_catalog_reference(
            provider_code="",
            provider_kind="test",
            canonical_symbol="EURUSD",
            asset_class="fx",
            base_currency="EUR",
            quote_currency="USD",
            digits=5,
            tick_size=Decimal("0.00001"),
            min_volume=Decimal("0.01"),
            max_volume=Decimal(100),
            volume_step=Decimal("0.01"),
            request_id=_REQUEST_ID,
        )
