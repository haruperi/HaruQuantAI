"""Demonstrate FEAT-BRK-00 Instrument and Venue Profiles."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.kernel.identity import generate_id
from app.services.brokers import (
    build_instrument_venue_profile,
    get_broker_value_field,
    parse_instrument_venue_profile,
    register_broker_symbol_mapping,
    resolve_broker_canonical_symbol,
    resolve_broker_provider_symbol,
    resolve_broker_provider_symbol_as_of,
    run_broker_migrations,
)
from app.services.data import (
    build_data_settings,
    data_settings_context,
    run_data_migrations,
)

_EFFECTIVE_FROM = "2026-01-01T00:00:00+00:00"


def _show(label: str, result: object) -> None:
    """Print separate success and substantive-data evidence.

    Args:
        label: Functional-requirement evidence label.
        result: Data-owned standard transaction response.
    """
    status = get_broker_value_field(result, "status")
    data = get_broker_value_field(result, "data")
    print(f"SUCCESS {label}: {status}")
    print(f"DATA {label}: {data!r}")


def _prepare_mapping(request_id: str) -> None:
    """Create one bounded identity mapping for read evidence.

    Args:
        request_id: Canonical request identifier.
    """
    result = register_broker_symbol_mapping(
        "mt5",
        "EURUSD",
        "EURUSD.r",
        request_id=request_id,
        effective_from=_EFFECTIVE_FROM,
        contract_size="100000",
        digits_override=5,
    )
    _show("mapping setup", result)


def fr_brokers_142_current_provider_symbol(request_id: str) -> None:
    """Resolve the current provider symbol.

    Args:
        request_id: Canonical request identifier.
    """
    _show(
        "FR-BRK-142 current provider symbol",
        resolve_broker_provider_symbol("mt5", "EURUSD", request_id=request_id),
    )


def fr_brokers_143_reverse_canonical_symbol(request_id: str) -> None:
    """Resolve the current canonical symbol.

    Args:
        request_id: Canonical request identifier.
    """
    _show(
        "FR-BRK-143 reverse canonical symbol",
        resolve_broker_canonical_symbol("mt5", "EURUSD.r", request_id=request_id),
    )


def fr_brokers_144_historical_provider_symbol(request_id: str) -> None:
    """Resolve the provider symbol at a historical instant.

    Args:
        request_id: Canonical request identifier.
    """
    _show(
        "FR-BRK-144 historical provider symbol",
        resolve_broker_provider_symbol_as_of(
            "mt5",
            "EURUSD",
            "2026-06-01T00:00:00+00:00",
            request_id=request_id,
        ),
    )


def fr_brokers_147_profile_evidence() -> None:
    """Build and parse complete immutable instrument-profile evidence."""
    profile = build_instrument_venue_profile(
        broker="mt5",
        provider_symbol="EURUSD.r",
        canonical_symbol="EURUSD",
        asset_class="FX",
        venue="mt5-demo",
        tick_size="0.00001",
        price_precision=5,
        quantity_step="0.01",
        contract_multiplier="100000",
        currency="USD",
        session_calendar={"monday": "00:00-23:59"},
        order_types=("MARKET", "LIMIT", "STOP"),
        time_in_force=("GTC", "DAY"),
        margin_eligible=True,
        shortable=True,
        settlement="T+2",
        halt_state="OPEN",
        lifecycle_eligibility="TRADEABLE",
        source_timestamp=datetime(2026, 8, 10, tzinfo=UTC),
    )
    parsed = parse_instrument_venue_profile(profile)
    print("SUCCESS FR-BRK-147 profile evidence: validated")
    print(f"DATA FR-BRK-147 profile evidence: {parsed!r}")


def main() -> None:
    """Run all FEAT-BRK-00 evidence against an isolated dev database."""
    with TemporaryDirectory(prefix="feat-brk-00-") as temporary:
        root = Path(temporary)
        (root / "data/cache").mkdir(parents=True)
        (root / "data/raw").mkdir(parents=True)
        settings = build_data_settings(
            database_url="sqlite:///data/cache/brokers.sqlite3",
            data_dir=root,
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(Path("data/raw"), Path("data/cache")),
        )
        request_id = generate_id("req")
        with data_settings_context(settings):
            run_data_migrations(request_id)
            run_broker_migrations(request_id)
            _prepare_mapping(request_id)
            fr_brokers_142_current_provider_symbol(request_id)
            fr_brokers_143_reverse_canonical_symbol(request_id)
            fr_brokers_144_historical_provider_symbol(request_id)
            fr_brokers_147_profile_evidence()


if __name__ == "__main__":
    main()
