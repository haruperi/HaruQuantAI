"""Demonstrate FEAT-DATA-18 application-triggered catalog evidence."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_settings,
    data_settings_context,
    get_catalog_table_lifecycles,
    get_verified_research_source,
    reconcile_data_catalog,
    record_catalog_fetch,
    record_catalog_quality_event,
    run_data_migrations,
    sync_catalog_reference,
)
from app.utils import generate_id


def main() -> None:
    """Run bounded reference, telemetry, reconciliation, and lifecycle evidence."""
    print(
        "INPUT DATA: one explicit provider, symbol, session, fetch, and quality event"
    )
    with TemporaryDirectory(prefix="feat-data-18-") as temporary:
        root = Path(temporary)
        (root / "data/cache").mkdir(parents=True)
        (root / "data/raw").mkdir(parents=True)
        settings = build_data_settings(
            database_url="sqlite:///data/cache/catalog.sqlite3",
            data_dir=root,
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(Path("data/raw"), Path("data/cache")),
        )
        request_id = generate_id("req")
        now = datetime(2026, 8, 5, tzinfo=UTC)
        with data_settings_context(settings):
            run_data_migrations(request_id)
            reference = sync_catalog_reference(
                provider_code="usage",
                provider_kind="recorded",
                canonical_symbol="EURUSD",
                asset_class="fx",
                base_currency="EUR",
                quote_currency="USD",
                digits=5,
                tick_size=Decimal("0.00001"),
                min_volume=Decimal("0.01"),
                max_volume=Decimal(100),
                volume_step=Decimal("0.01"),
                request_id=request_id,
                observed_at=now,
            )
            record_catalog_fetch(
                values=(
                    "fetch-usage",
                    "provider-usage",
                    "symbol-usage",
                    "bars",
                    "M1",
                    1,
                    2,
                    1,
                    0,
                    None,
                    "recorded",
                    1,
                    "success",
                    None,
                    request_id,
                    "",
                    now.isoformat(),
                    now.isoformat(),
                    now.isoformat(),
                    now.isoformat(),
                ),
                request_id=request_id,
            )
            record_catalog_quality_event(
                values=(
                    "quality-usage",
                    "symbol-usage",
                    None,
                    None,
                    "fetch-usage",
                    "gap",
                    "warning",
                    "inspect",
                    1,
                    2,
                    1,
                    "{}",
                    now.isoformat(),
                    request_id,
                    "",
                    now.isoformat(),
                ),
                request_id=request_id,
            )
            rebuild = reconcile_data_catalog(request_id=request_id)
            verified = get_verified_research_source(
                "missing", "v1", request_id=request_id
            )
            actual = {
                "reference_rows": reference.affected_rows,
                "table_lifecycles": len(get_catalog_table_lifecycles()),
                "rebuild": rebuild,
                "verified_source": verified,
            }
    print(f"ACTUAL DATA: {actual}")
    print("SUCCESS: FEAT-DATA-18 completed")


if __name__ == "__main__":
    main()
