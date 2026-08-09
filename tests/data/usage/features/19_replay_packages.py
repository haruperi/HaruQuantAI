# ruff: noqa: BLE001
"""Demonstrate FEAT-DATA-19 deterministic no-lookahead replay data packages."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_settings,
    build_replay_package,
    data_settings_context,
    parse_replay_package,
    run_data_migrations,
    stream_replay_events,
)
from app.utils import generate_id


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def fr_data_181() -> object:
    """FR-DATA-181: Stage 1 — Build and JSON-round-trip a bounded replay package."""
    _header("Stage 1: Replay Package Construction (FR-DATA-181)")
    package = build_replay_package(
        source_id="mt5",
        symbols=("EURUSD",),
        data_kind="ticks",
        start=datetime(2026, 6, 1, tzinfo=UTC),
        end=datetime(2026, 6, 2, tzinfo=UTC),
        request_id=generate_id("req"),
    )
    print(_format_result(package))
    mapping = package.model_dump(mode="json")
    reparsed = parse_replay_package(mapping)
    print(f"Data -> ReplayPackage(round_trip_equal={reparsed == package})")
    return package


def fr_data_182_183(package: object) -> None:
    """FR-DATA-182/183: Stage 2 — Stream deterministic-order, no-lookahead replay events."""
    _header("Stage 2: Deterministic No-Lookahead Replay Streaming (FR-DATA-182/183)")
    as_of = datetime.now(UTC)
    try:
        events = list(stream_replay_events(package, as_of=as_of))  # type: ignore[arg-type]
        print(f"Data -> ReplayEvent(count={len(events)}, as_of={as_of.isoformat()})")
        if events:
            first = events[0]
            print(
                f"Data -> ReplayEvent(sequence={first.sequence}, symbol={first.symbol}, "
                f"available_at={first.available_at.isoformat()})"
            )
    except Exception as exc:
        print(f"Output Result -> {type(exc).__name__} : {type(exc).__name__}")
        print(f"Data -> Exception({exc})")

    # Fail-closed proof: a boundary before any coverage yields zero events.
    try:
        past_events = list(
            stream_replay_events(  # type: ignore[arg-type]
                package, as_of=datetime(2000, 1, 1, tzinfo=UTC)
            )
        )
        print(f"Data -> ReplayEvent(fail_closed_past_count={len(past_events)})")
    except Exception as exc:
        print(f"Output Result -> {type(exc).__name__} : {type(exc).__name__}")
        print(f"Data -> Exception({exc})")


def main() -> None:
    """Execute every functional-requirement demonstration."""
    with TemporaryDirectory(prefix="usage-replay-") as directory:
        (Path(directory) / "data" / "raw").mkdir(parents=True, exist_ok=True)
        settings = build_data_settings(
            database_url="sqlite:///usage.sqlite3",
            data_dir=Path(directory),
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(
                Path("raw"),
                Path("processed"),
                Path("data"),
                Path("data/raw"),
                Path("data/processed"),
            ),
            data_provider_sources=("mt5",),
            data_raw_root=Path("data/raw"),
        )
        with data_settings_context(settings):
            run_data_migrations(generate_id("req"))
            print("=" * 80)
            print("FEATURE: FEAT-DATA-19 - Replay Data Package")
            print(
                "PURPOSE: Deterministic, no-lookahead replay of bounded evidence with explicit availability timestamps"
            )
            print(
                "MODULE FLOW: Stage 1 (Package Construction) -> Stage 2 (Deterministic No-Lookahead Streaming)"
            )
            print("=" * 80)

            package = fr_data_181()
            fr_data_182_183(package)
            print("SUCCESS: FEAT-DATA-19 completed")


if __name__ == "__main__":
    main()
