"""Market Data Physical Storage Layout, Schemas, and Integrity Verification.

Description:
    Defines the immutable physical storage layout, strict PyArrow tabular
    schemas, partition path resolution, and cryptographic checksum verification
    for persisted quantitative market data (ticks and M1 bars).

    External relations and workflows:
    - Market persistence facade: Consumed by `app.persistence.market`
      (`MarketDataStore`) during parquet chunk ingestion, batch reading,
      catalog reconciliation, and symbol export workflows.
    - Data source plugins: Ingestion plugins (such as Dukascopy acquisition)
      lower downloaded historical data into these standardized Parquet schemas
      and canonical partition paths.

    Internal coordination:
    - TICK_SCHEMA & M1_SCHEMA: Fixed PyArrow schemas enforcing millisecond UTC
      timestamps, 64-bit integer tick pricing / volumes, and double-precision
      floating-point bar OHLC values.
    - MarketFile: Immutable dataclass modeling committed market file metadata
      (digest, row count, byte size, millisecond coverage ranges).
    - resolve_market_path: Validates naming tokens, maps (source, kind, symbol,
      period) into hierarchical directories, and rejects symlink traversal.
    - verify_market_file: Validates disk path alignment and computes streaming
      SHA-256 digests to ensure zero file tampering.

Purpose:
    FEAT-PERSIST-MARKET-FILES: Physical parquet schemas, canonical partition
    layouts, and streaming digest verification for historical market data.

Key Capabilities:
    - FR-PERSIST-MARKET-FILES-PATH: Computes canonical partitioned paths for tick
      and M1 datasets while preventing symlink attacks and path traversal via
      resolve_market_path().
      * Verified via: logger.debug("Resolved canonical market path: %s")
    - FR-PERSIST-MARKET-FILES-VERIFY: Streams SHA-256 checksums to verify disk
      file integrity and catalog consistency via verify_market_file().
      * Verified via: logger.debug("Verified market file integrity: %s "
        "(digest=%s)")

Python API Usage:
    ```python
    from pathlib import Path

    from app.persistence.market_files import resolve_market_path

    path = resolve_market_path(
        data_root=Path("data"),
        source="dukascopy",
        kind="m1",
        symbol="eurusd",
        period="2025",
    )
    ```

CLI Usage:
    ```bash
    # Verified through persistence market test suite:
    uv run python -m pytest tests/persistence/test_market.py
    ```
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pyarrow as pa  # type: ignore[import-untyped]

from app.host.logging import get_logger

logger = get_logger(__name__)

Kind = Literal["ticks", "m1"]
SYMBOL = re.compile(r"^[a-z0-9_]{2,40}$")
SOURCE = re.compile(r"^[a-z][a-z0-9_]{1,39}$")
BATCH_ROWS = 8192
MAX_DATASET_LABEL = 80
MAX_DEFINITION_BATCH = 725

TICK_SCHEMA = pa.schema(
    [
        pa.field("DateTime", pa.timestamp("ms", tz="UTC"), nullable=False),
        pa.field("Ask", pa.int64(), nullable=False),
        pa.field("Bid", pa.int64(), nullable=False),
        pa.field("Volume", pa.uint64(), nullable=False),
    ]
)

M1_SCHEMA = pa.schema(
    [
        pa.field("DateTime", pa.timestamp("ms", tz="UTC"), nullable=False),
        *(
            pa.field(name, pa.float64(), nullable=False)
            for name in ("Open", "High", "Low", "Close")
        ),
        pa.field("Volume", pa.uint64(), nullable=False),
    ]
)


@dataclass(frozen=True)
class MarketFile:
    """A committed market-file revision, independent of its producer."""

    source: str
    kind: Kind
    symbol: str
    period: str
    relative_path: str
    revision: int
    sha256: str
    byte_size: int
    row_count: int
    first_ms: int
    last_ms: int
    coverage: tuple[tuple[int, int], ...]
    provider_mode: str


def resolve_market_path(
    data_root: Path, source: str, kind: Kind, symbol: str, period: str
) -> Path:
    """Construct one canonical relative path from checked components.

    Raises:
        ValueError: When inputs are invalid or path contains symlinks/traversal.
    """
    if not SOURCE.fullmatch(source) or not SYMBOL.fullmatch(symbol):
        raise ValueError("Invalid market identity")
    if kind == "m1":
        if not re.fullmatch(r"20\d{2}|19\d{2}", period):
            raise ValueError("Invalid M1 period")
        relative = Path("market", source, "m1", symbol, f"{period}.parquet")
    elif kind == "ticks":
        if not re.fullmatch(r"(?:19|20)\d{2}-(?:0[1-9]|1[0-2])", period):
            raise ValueError("Invalid tick period")
        year, month = period.split("-")
        month_name = (
            "jan",
            "feb",
            "mar",
            "apr",
            "may",
            "jun",
            "jul",
            "aug",
            "sep",
            "oct",
            "nov",
            "dec",
        )[int(month) - 1]
        relative = Path(
            "market",
            source,
            "ticks",
            symbol,
            year,
            f"{month}-{month_name}.parquet",
        )
    else:
        raise ValueError("Invalid market kind")
    path = data_root / relative
    if any(item.is_symlink() or item.is_junction() for item in (path, *path.parents)):
        raise ValueError("Linked market path")
    logger.debug("Resolved canonical market path: %s", path)
    return path


def verify_market_file(data_root: Path, record: MarketFile) -> Path:
    """Resolve and digest-check one catalog entry before handing it to readers."""
    path = resolve_market_path(
        data_root, record.source, record.kind, record.symbol, record.period
    )
    if path.relative_to(data_root).as_posix() != record.relative_path:
        raise ValueError("Market catalog path mismatch")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != record.sha256:
        raise ValueError("Market file digest mismatch")
    logger.debug(
        "Verified market file integrity: %s (digest=%s)",
        path,
        record.sha256,
    )
    return path
