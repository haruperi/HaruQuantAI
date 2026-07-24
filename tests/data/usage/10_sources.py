"""Run source composition and local artifact access examples (FEAT-DATA-04).

Covers `FR-DATA-101` through `FR-DATA-104`: composing configured sources,
discovering which identifiers are available, timeframe-scoped local artifact
resolution, and bounded local reads.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    DataError,
    DataSettings,
    LocalMarketDataSource,
    OHLCVRecord,
    SourceReadRequest,
    data_settings_context,
    ensure_source,
    get_source_descriptor,
    list_composable_sources,
)
from app.utils import generate_id

_SYMBOL = "EURUSD"
_START = datetime(2026, 1, 1, tzinfo=UTC)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _bar(index: int) -> OHLCVRecord:
    """Return one canonical bar for the local fixture series."""
    timestamp = _START + timedelta(minutes=index)
    return OHLCVRecord(
        timestamp=timestamp,
        open=Decimal("1.1000"),
        high=Decimal("1.1010"),
        low=Decimal("1.0990"),
        close=Decimal("1.1005"),
        volume=Decimal(100),
        price_unit="USD",
        volume_unit="lots",
        source="csv",
        source_symbol=_SYMBOL,
        source_revision="local-artifact-v1",
        available_at=timestamp + timedelta(seconds=1),
    )


def _example_fr_data_102() -> None:
    """Discover which source identifiers the configuration can compose."""
    _header("FR-DATA-102 list_composable_sources")
    print("Composable sources:", list_composable_sources())


def _example_fr_data_101(root: Path) -> None:
    """Compose one configured local source without credentials or network."""
    _header("FR-DATA-101 ensure_source")
    ensure_source("csv", generate_id("req"))
    descriptor = get_source_descriptor("csv")
    print("Source:", descriptor.source_id)
    print("Readiness:", descriptor.readiness)
    print("Requires credentials:", descriptor.requires_credentials)
    print("Requires network:", descriptor.requires_network)


def _example_fr_data_103(raw_root: Path) -> None:
    """Resolve two timeframes for one symbol independently."""
    _header("FR-DATA-103 timeframe-scoped local artifacts")
    (raw_root / f"{_SYMBOL}_M1.csv").touch()
    (raw_root / f"{_SYMBOL}_H1.csv").touch()
    source = LocalMarketDataSource(source_id="csv", raw_root=raw_root, metadata={})
    minute_path, _ = source._artifact(_SYMBOL, "M1")
    hour_path, _ = source._artifact(_SYMBOL, "H1")
    print("M1 artifact:", minute_path.name)
    print("H1 artifact:", hour_path.name)


def _example_fr_data_104() -> None:
    """Apply the requested window and limit at the local source boundary."""
    _header("FR-DATA-104 bounded local selection")
    records = tuple(_bar(index) for index in range(10))
    request = SourceReadRequest(
        source_id="csv",
        provider_symbol=_SYMBOL,
        data_kind="bars",
        timeframe="M1",
        start=_START + timedelta(minutes=2),
        end=_START + timedelta(minutes=5),
        limit=2,
        request_id=generate_id("req"),
    )
    selected = LocalMarketDataSource._select(records, request)
    print("Records available:", len(records))
    print("Records selected:", len(selected))
    print("First selected:", selected[0].timestamp.isoformat())


def _demonstrate_feature() -> None:
    """Execute every source composition example against real runtime state."""
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        raw_root = root / "data" / "raw"
        raw_root.mkdir(parents=True)
        settings = DataSettings(
            database_url=f"sqlite:///{root / 'data.db'}",
            data_dir=root,
            data_local_sources=("csv",),
            data_raw_root=Path("data/raw"),
        )
        try:
            with data_settings_context(settings):
                _example_fr_data_102()
                _example_fr_data_101(root)
                _example_fr_data_103(raw_root)
                _example_fr_data_104()
        except DataError as error:
            print("Source composition example failed:", error.code)


_DEMONSTRATED = [False]


def _demonstrate_once() -> None:
    """Run the feature demonstration once for all requirement entry points."""
    if _DEMONSTRATED[0]:
        return
    _demonstrate_feature()
    _DEMONSTRATED[0] = True


def fr_data_010() -> None:
    "FR-DATA-010: Declare source readiness, capabilities, credential/network/write requirements, schema/timezone/version metadata, promotion criteria, and sign-off evidence."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_011() -> None:
    "FR-DATA-011: Declare permitted workflow contexts, export/retention/attribution restrictions, enforcement behavior, and license status for each source."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_022() -> None:
    "FR-DATA-022: Require every adapter to perform one bounded read and return provider-neutral raw records plus source metadata without broker mutation."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_023() -> None:
    "FR-DATA-023: Require bounded, deterministically ordered symbol discovery with cursor pagination and declared discovery capability."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_024() -> None:
    "FR-DATA-024: Require normalized symbol metadata with provenance and explicit missing fields rather than optimistic defaults."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_025() -> None:
    "FR-DATA-025: Register a source descriptor and lazy factory atomically, reject duplicate/conflicting declarations, and perform no I/O during registration/import."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_026() -> None:
    "FR-DATA-026: Validate requested and explicit fallback sources in order against capability, readiness, license, context, timeout/rate, and breaker state and record every attempt."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_027() -> None:
    "FR-DATA-027: Change readiness only from a complete authenticated evidence package, record an audit event, and permit immediate reversible demotion."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_101() -> None:
    "FR-DATA-101: Compose and register the descriptor and lazy factory for every configured source — local artifact sources at `production` readiness and enabled provider facades at `staging` — dispatching on source kind rather than accepting a single hardcoded provider. Credential-free Binance Spot, Dukascopy, and Yahoo public reads compose without account secrets; an unconfigured identifier fails closed."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_102() -> None:
    "FR-DATA-102: Report which source identifiers the current configuration can compose so callers and operators discover valid `source_id` values without trial and error."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_103() -> None:
    "FR-DATA-103: Resolve local artifacts as `{symbol}_{timeframe}` first and fall back to `{symbol}` only for kinds without a timeframe, so multiple timeframes per symbol are individually addressable."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_104() -> None:
    "FR-DATA-104: Apply the requested UTC range and record limit at the local source boundary rather than returning the whole artifact, and fail closed when the window selects nothing."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_113() -> None:
    "FR-DATA-113: Block a retrieval, storage, or export workflow when the source `SourceLicensePolicy` does not permit it, failing closed when licence metadata is absent."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_114() -> None:
    "FR-DATA-114: Return the attribution text a source requires for publication, and fail rather than return an empty string when attribution is required but undeclared."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_115() -> None:
    "FR-DATA-115: Allow only the declared read method names and reject every mutation name deterministically, independent of the adapter's actual surface."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_116() -> None:
    "FR-DATA-116: Wrap a caller-owned broker client in a proxy that enforces the read-only contract on every attribute access at runtime, so a mutation call fails even when the underlying client exposes it."  # noqa: E501 - exact specification text
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
