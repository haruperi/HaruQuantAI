# ruff: noqa: BLE001
"""Demonstrate FEAT-DATA-02 dataset lifecycle and revision history."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from _artifact_catalog_support import main as run_catalog_support
from _persistence_support import main as run_persistence_support
from app.kernel.identity import generate_id
from app.kernel.serialization import canonical_digest
from app.services.data import (
    build_data_settings,
    build_dataset_load_request,
    build_dataset_save_request,
    build_synthetic_request,
    data_settings_context,
    generate_synthetic_bars,
    get_provider_specification_revision,
    get_provider_specification_revisions,
    list_verified_datasets,
    load_csv,
    load_local_dataset,
    load_parquet,
    register_provider_specification_revision,
    run_data_migrations,
    save_market_data,
    to_ohlcv_dataframe,
)

_CSV_PATH = Path("data/raw/EURUSD_H1.csv")
_PARQUET_PATH = Path("data/raw/EURUSD_H1.parquet")
_SPEC_OBSERVED = datetime(2026, 8, 15, 10, tzinfo=UTC)


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
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _ensure_raw_datasets() -> None:
    """Ensure manifest-backed CSV and Parquet datasets exist in approved raw directory."""
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    req_id = generate_id("req")
    synth_req = build_synthetic_request(
        symbol="EURUSD",
        data_kind="bars",
        timeframe="H1",
        start=datetime(2026, 6, 1, tzinfo=UTC),
        record_count=24,
        method="gbm",
        seed=42,
        parameters={
            "mu": Decimal("0.02"),
            "sigma": Decimal("0.10"),
            "start_val": Decimal("1.1000"),
        },
        precision_policy="decimal_string",
        request_id=req_id,
    )
    synth_res = generate_synthetic_bars(synth_req)
    if synth_res.data is None:
        raise RuntimeError("Failed to generate synthetic bars")
    dataset = synth_res.data
    save_market_data(
        build_dataset_save_request(
            dataset=dataset,
            relative_path=_CSV_PATH,
            format="csv",
            overwrite=True,
            request_id=req_id,
        )
    )
    save_market_data(
        build_dataset_save_request(
            dataset=dataset,
            relative_path=_PARQUET_PATH,
            format="parquet",
            overwrite=True,
            request_id=req_id,
        )
    )


def fr_data_016() -> None:
    """FR-DATA-016: Stage 1 — Construct DatasetLoadRequest boundary for path resolution under approved roots."""
    _header("Stage 1: Load Request Construction - Dataset Load Request (FR-DATA-016)")
    request = build_dataset_load_request(
        relative_path=_CSV_PATH,
        format="csv",
        request_id=generate_id("req"),
    )
    print(_format_result(request))
    print(
        f"Data -> DatasetLoadRequest(path={request.relative_path}, format={request.format})"
    )


def fr_data_017_csv() -> None:
    """FR-DATA-017: Stage 2 — Load a local CSV file directly via load_csv with manifest verification."""
    _header("Stage 2: Direct CSV Loading - Load CSV Dataset (FR-DATA-017)")
    _ensure_raw_datasets()
    try:
        response = load_csv(_CSV_PATH)
        print(_format_result(response))
        if response.status == "success" and response.data is not None:
            ds = response.data
            print(
                f"Data -> MarketDataset(symbol={ds.symbol}, records={ds.record_count})"
            )
            df = to_ohlcv_dataframe(ds)
            print(f"Data -> DataFrame shape={df.shape}")
    except Exception as exc:
        print(f"Output Result -> {type(exc).__name__} : {type(exc).__name__}")
        print(f"Data -> Exception({exc})")


def fr_data_017_parquet() -> None:
    """FR-DATA-017: Stage 3 — Load a local Parquet file directly via load_parquet with manifest verification."""
    _header("Stage 3: Direct Parquet Loading - Load Parquet Dataset (FR-DATA-017)")
    _ensure_raw_datasets()
    try:
        response = load_parquet(_PARQUET_PATH)
        print(_format_result(response))
        if response.status == "success" and response.data is not None:
            ds = response.data
            print(
                f"Data -> MarketDataset(symbol={ds.symbol}, records={ds.record_count})"
            )
            df = to_ohlcv_dataframe(ds)
            print(f"Data -> DataFrame shape={df.shape}")
    except Exception as exc:
        print(f"Output Result -> {type(exc).__name__} : {type(exc).__name__}")
        print(f"Data -> Exception({exc})")


def fr_data_017_018_governed() -> None:
    """FR-DATA-017, FR-DATA-018: Stage 4 — Fetch a local dataset through typed load_local_dataset request boundary."""
    _header(
        "Stage 4: Manifest-Verifying Governed Load - Governed Load (FR-DATA-017, FR-DATA-018)"
    )
    _ensure_raw_datasets()
    request = build_dataset_load_request(
        relative_path=_CSV_PATH,
        format="csv",
        request_id=generate_id("req"),
    )
    try:
        response = load_local_dataset(request)
        print(_format_result(response))
        if response.status == "success" and response.data is not None:
            ds = response.data
            print(
                f"Data -> MarketDataset(symbol={ds.symbol}, records={ds.record_count})"
            )
    except Exception as exc:
        print(f"Output Result -> {type(exc).__name__} : {type(exc).__name__}")
        print(f"Data -> Exception({exc})")


def _provider_snapshot(observed_at: datetime, revision: str) -> dict[str, object]:
    """Return one bounded canonical provider snapshot mapping."""
    payload: dict[str, object] = {
        "broker": "mt5",
        "server": "demo-server",
        "environment": "demo",
        "account_digest": "a" * 64,
        "provider_symbol": "EURUSD",
        "terminal_build": "5000",
        "source_revision": revision,
        "observed_at": observed_at.isoformat(),
        "retrieval_provenance": "sanitized-demo-fixture",
    }
    payload["checksum"] = canonical_digest(payload)
    return payload


def fr_data_214() -> None:
    """FR-DATA-214: Persist one immutable checksummed specification revision."""
    _header("Provider Specification Revision Registration (FR-DATA-214)")
    result = register_provider_specification_revision(
        _provider_snapshot(_SPEC_OBSERVED, "r1"), request_id=generate_id("req")
    )
    print(_format_result(result))
    print(f"Data -> revision={result['revision_id']}")


def fr_data_215() -> None:
    """FR-DATA-215: Supersede the open revision without overlap."""
    _header("Atomic Provider Specification Supersession (FR-DATA-215)")
    observed_at = _SPEC_OBSERVED + timedelta(hours=1)
    result = register_provider_specification_revision(
        _provider_snapshot(observed_at, "r2"), request_id=generate_id("req")
    )
    print(_format_result(result))
    print(f"Data -> supersedes={result['supersedes_revision_id']}")


def fr_data_216() -> None:
    """FR-DATA-216: Retrieve exact as-of and bounded coverage evidence."""
    _header("Point-in-Time Provider Specification Coverage (FR-DATA-216)")
    request_id = generate_id("req")
    identity = {
        "provider": "mt5",
        "server": "demo-server",
        "environment": "demo",
        "account_digest": "a" * 64,
        "symbol": "EURUSD",
        "request_id": request_id,
    }
    point = get_provider_specification_revision(**identity, as_of=_SPEC_OBSERVED)
    interval = get_provider_specification_revisions(
        **identity,
        interval_start=_SPEC_OBSERVED,
        interval_end=_SPEC_OBSERVED + timedelta(hours=2),
    )
    print(_format_result(point))
    print(
        "Data -> "
        f"as_of_covered={point['complete_coverage']}, "
        f"interval_revisions={len(interval['revisions'])}"
    )


def main() -> None:
    """Execute every functional-requirement demonstration."""
    with TemporaryDirectory(prefix="usage-local-data-") as directory:
        base_dir = Path(directory)
        settings = build_data_settings(
            database_url="sqlite:///usage.sqlite3",
            data_dir=base_dir,
            approved_storage_roots=(Path("data/raw"), Path("data/processed")),
            data_raw_root=Path("data/raw"),
        )
        with data_settings_context(settings):
            run_data_migrations(generate_id("req"))
            print("=" * 80)
            print("FEATURE: FEAT-DATA-02 - Dataset Lifecycle")
            print(
                "PURPOSE: DatasetLoadRequest, manifest verification, CSV/Parquet loaders, and load_local_dataset"
            )
            print(
                "MODULE FLOW: Stage 1 (Load Request Construction) -> Stage 2 (Direct CSV Loading) -> Stage 3 (Direct Parquet Loading) -> Stage 4 (Manifest-Verifying Governed Load)"
            )
            print("=" * 80)

            fr_data_016()
            fr_data_017_csv()
            fr_data_017_parquet()
            fr_data_017_018_governed()
            fr_data_214()
            fr_data_215()
            fr_data_216()
            print(_format_result(list_verified_datasets(request_id=generate_id("req"))))
            print("SUCCESS: FEAT-DATA-02 completed")
    run_persistence_support()
    run_catalog_support()


if __name__ == "__main__":
    main()
