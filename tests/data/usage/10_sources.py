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

from app.services.data._settings import DataSettings, data_settings_context
from app.services.data.contracts import DataError, OHLCVRecord
from app.services.data.sources.composition import ensure_source, list_composable_sources
from app.services.data.sources.contracts import (
    SourceReadRequest,
)
from app.services.data.sources.local_adapter import LocalMarketDataSource
from app.services.data.sources.registry import _reset_registry, get_source_descriptor
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


def example_fr_data_102_composable_sources() -> None:
    """Discover which source identifiers the configuration can compose."""
    _header("FR-DATA-102 list_composable_sources")
    print("Composable sources:", list_composable_sources())


def example_fr_data_101_source_composition(root: Path) -> None:
    """Compose one configured local source without credentials or network."""
    _header("FR-DATA-101 ensure_source")
    ensure_source("csv", generate_id("req"))
    descriptor = get_source_descriptor("csv")
    print("Source:", descriptor.source_id)
    print("Readiness:", descriptor.readiness)
    print("Requires credentials:", descriptor.requires_credentials)
    print("Requires network:", descriptor.requires_network)


def example_fr_data_103_timeframe_scoped_artifact(raw_root: Path) -> None:
    """Resolve two timeframes for one symbol independently."""
    _header("FR-DATA-103 timeframe-scoped local artifacts")
    (raw_root / f"{_SYMBOL}_M1.csv").touch()
    (raw_root / f"{_SYMBOL}_H1.csv").touch()
    source = LocalMarketDataSource(source_id="csv", raw_root=raw_root, metadata={})
    minute_path, _ = source._artifact(_SYMBOL, "M1")
    hour_path, _ = source._artifact(_SYMBOL, "H1")
    print("M1 artifact:", minute_path.name)
    print("H1 artifact:", hour_path.name)


def example_fr_data_104_bounded_local_fetch() -> None:
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


def main() -> None:
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
        _reset_registry()
        try:
            with data_settings_context(settings):
                example_fr_data_102_composable_sources()
                example_fr_data_101_source_composition(root)
                example_fr_data_103_timeframe_scoped_artifact(raw_root)
                example_fr_data_104_bounded_local_fetch()
        except DataError as error:
            print("Source composition example failed:", error.code)
        finally:
            _reset_registry()


if __name__ == "__main__":
    main()
