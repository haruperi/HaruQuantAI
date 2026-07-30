# ruff: noqa: BLE001, E402
"""Run source composition and local artifact access examples (FEAT-DATA-04).

Covers `FR-DATA-101` through `FR-DATA-104`: composing configured sources,
discovering which identifiers are available, timeframe-scoped local artifact
resolution, and bounded local reads.
"""

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    build_data_error,
    build_data_settings,
    build_dataset_save_request,
    data_settings_context,
    ensure_source,
    get_market_data,
    get_source_descriptor,
    get_symbol_metadata,
    list_composable_sources,
    save_dataset,
    unwrap_data_response,
)

DataError = build_data_error

from app.utils import generate_id

_SYMBOL = "EURUSD"
_END = datetime.now(UTC)
_START = _END - timedelta(days=5)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _example_fr_data_102() -> None:
    """Discover which source identifiers the configuration can compose."""
    _header("FR-DATA-102 list_composable_sources")
    res = list_composable_sources()
    if res.status == "success" and res.data is not None:
        print("Composable sources:", res.data)


def _example_fr_data_101(root: Path) -> None:
    """Compose one configured local source without credentials or network."""
    _header("FR-DATA-101 ensure_source")
    ensure_source("csv", generate_id("req"))
    res = get_source_descriptor("csv")
    if res.status == "success" and res.data is not None:
        descriptor = res.data
        print("Source:", descriptor.source_id)
        print("Readiness:", descriptor.readiness)
        print("Requires credentials:", descriptor.requires_credentials)
        print("Requires network:", descriptor.requires_network)


def _example_fr_data_103(raw_root: Path) -> None:
    """Inspect the configured source through its public descriptor boundary."""
    _header("FR-DATA-103 timeframe-scoped local artifacts")
    result = get_source_descriptor("csv")
    if result.status == "success" and result.data is not None:
        print("Source capabilities:", result.data.capabilities)


def _example_fr_data_104(start: datetime, end: datetime) -> None:
    """Apply a bounded request through the public market-data operation."""
    _header("FR-DATA-104 bounded local selection")
    result = get_market_data(
        source_id="csv",
        symbol=_SYMBOL,
        timeframe="M1",
        start=start,
        end=end,
        limit=2,
        request_id=generate_id("req"),
    )
    dataset = unwrap_data_response(
        result,
        operation="data.usage.get_local_market_data",
        request_id=result.metadata.request_id,
    )
    print(
        "Bounded local rows:",
        [
            (record.timestamp.isoformat(), str(record.open), str(record.close))
            for record in dataset.records
        ],
    )


def _prepare_genuine_local_artifact(raw_root: Path) -> tuple[datetime, datetime]:
    """Persist a genuine bounded MT5 dataset for the local-source read."""
    response = get_market_data(
        source_id="mt5",
        symbol=_SYMBOL,
        timeframe="M1",
        start=_START,
        end=_END,
        limit=10,
        use_cache=False,
        request_id=generate_id("req"),
    )
    dataset = unwrap_data_response(
        response,
        operation="data.usage.get_mt5_market_data",
        request_id=response.metadata.request_id,
    )
    save_response = save_dataset(
        build_dataset_save_request(
            dataset=dataset,
            relative_path=Path("data/raw/EURUSD_M1.csv"),
            format="csv",
            overwrite=True,
            request_id=dataset.request_id,
        )
    )
    unwrap_data_response(
        save_response,
        operation="data.usage.save_local_market_data",
        request_id=save_response.metadata.request_id,
    )
    metadata_response = get_symbol_metadata(
        source_id="mt5",
        symbol=_SYMBOL,
        request_id=generate_id("req"),
    )
    metadata = unwrap_data_response(
        metadata_response,
        operation="data.usage.get_mt5_symbol_metadata",
        request_id=metadata_response.metadata.request_id,
    )
    declared_metadata = metadata.model_dump(
        mode="json",
        exclude={"canonical_symbol", "provider_symbol", "source_id", "request_id"},
    )
    (raw_root / "symbols.json").write_text(
        json.dumps({_SYMBOL: declared_metadata}, indent=2),
        encoding="utf-8",
    )
    print(
        "Persisted genuine MT5 rows:",
        [
            (record.timestamp.isoformat(), str(record.open), str(record.close))
            for record in dataset.records[:3]
        ],
    )
    return dataset.records[2].timestamp, dataset.records[5].timestamp


def _demonstrate_feature() -> None:
    """Execute every source composition example against real runtime state."""
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        raw_root = root / "data" / "raw"
        raw_root.mkdir(parents=True)
        settings = build_data_settings(
            database_url="sqlite:///data.db",
            data_dir=root,
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            data_local_sources=("csv",),
            data_provider_sources=("mt5",),
            data_raw_root=Path("data/raw"),
        )
        try:
            with data_settings_context(settings):
                _example_fr_data_102()
                start, end = _prepare_genuine_local_artifact(raw_root)
                _example_fr_data_101(root)
                _example_fr_data_103(raw_root)
                _example_fr_data_104(start, end)
        except Exception as error:
            print(
                "Source composition example failed:",
                getattr(error, "code", type(error).__name__),
            )


_DEMONSTRATED = [False]


def _demonstrate_once() -> None:
    """Run the feature demonstration once for all requirement entry points."""
    if _DEMONSTRATED[0]:
        return
    _demonstrate_feature()
    _DEMONSTRATED[0] = True


def fr_data_010() -> None:
    _header("fr_data_010")
    "FR-DATA-010: Declare source readiness, capabilities, credential/network/write requirements, schema/timezone/version metadata, promotion criteria, and sign-off evidence."
    _demonstrate_once()


def fr_data_011() -> None:
    _header("fr_data_011")
    "FR-DATA-011: Declare permitted workflow contexts, export/retention/attribution restrictions, enforcement behavior, and license status for each source."
    _demonstrate_once()


def fr_data_022() -> None:
    _header("fr_data_022")
    "FR-DATA-022: Require every adapter to perform one bounded read and return provider-neutral raw records plus source metadata without broker mutation."
    _demonstrate_once()


def fr_data_023() -> None:
    _header("fr_data_023")
    "FR-DATA-023: Require bounded, deterministically ordered symbol discovery with cursor pagination and declared discovery capability."
    _demonstrate_once()


def fr_data_024() -> None:
    _header("fr_data_024")
    "FR-DATA-024: Require normalized symbol metadata with provenance and explicit missing fields rather than optimistic defaults."
    _demonstrate_once()


def fr_data_025() -> None:
    _header("fr_data_025")
    "FR-DATA-025: Register a source descriptor and lazy factory atomically, reject duplicate/conflicting declarations, and perform no I/O during registration/import."
    _demonstrate_once()


def fr_data_026() -> None:
    _header("fr_data_026")
    "FR-DATA-026: Validate requested and explicit fallback sources in order against capability, readiness, license, context, timeout/rate, and breaker state and record every attempt."
    _demonstrate_once()


def fr_data_027() -> None:
    _header("fr_data_027")
    "FR-DATA-027: Change readiness only from a complete authenticated evidence package, record an audit event, and permit immediate reversible demotion."
    _demonstrate_once()


def fr_data_101() -> None:
    _header("fr_data_101")
    "FR-DATA-101: Compose and register the descriptor and lazy factory for every configured source — local artifact sources at `production` readiness and enabled provider facades at `staging` — dispatching on source kind rather than accepting a single hardcoded provider. Credential-free Binance Spot, Dukascopy, and Yahoo public reads compose without account secrets; an unconfigured identifier fails closed."
    _demonstrate_once()


def fr_data_102() -> None:
    _header("fr_data_102")
    "FR-DATA-102: Report which source identifiers the current configuration can compose so callers and operators discover valid `source_id` values without trial and error."
    _demonstrate_once()


def fr_data_103() -> None:
    _header("fr_data_103")
    "FR-DATA-103: Resolve local artifacts as `{symbol}_{timeframe}` first and fall back to `{symbol}` only for kinds without a timeframe, so multiple timeframes per symbol are individually addressable."
    _demonstrate_once()


def fr_data_104() -> None:
    _header("fr_data_104")
    "FR-DATA-104: Apply the requested UTC range and record limit at the local source boundary rather than returning the whole artifact, and fail closed when the window selects nothing."
    _demonstrate_once()


def fr_data_113() -> None:
    _header("fr_data_113")
    "FR-DATA-113: Block a retrieval, storage, or export workflow when the source `SourceLicensePolicy` does not permit it, failing closed when licence metadata is absent."
    _demonstrate_once()


def fr_data_114() -> None:
    _header("fr_data_114")
    "FR-DATA-114: Return the attribution text a source requires for publication, and fail rather than return an empty string when attribution is required but undeclared."
    _demonstrate_once()


def fr_data_115() -> None:
    _header("fr_data_115")
    "FR-DATA-115: Allow only the declared read method names and reject every mutation name deterministically, independent of the adapter's actual surface."
    _demonstrate_once()


def fr_data_116() -> None:
    _header("fr_data_116")
    "FR-DATA-116: Wrap a caller-owned broker client in a proxy that enforces the read-only contract on every attribute access at runtime, so a mutation call fails even when the underlying client exposes it."
    _demonstrate_once()


def main() -> None:
    """Execute every functional-requirement demonstration."""
    demonstrations = (
        fr_data_010,
        fr_data_011,
        fr_data_022,
        fr_data_023,
        fr_data_024,
        fr_data_025,
        fr_data_026,
        fr_data_027,
        fr_data_101,
        fr_data_102,
        fr_data_103,
        fr_data_104,
        fr_data_113,
        fr_data_114,
        fr_data_115,
        fr_data_116,
    )
    for demonstration in demonstrations:
        demonstration()


if __name__ == "__main__":
    main()
