"""Typed host custody for canonical market partitions and independent readers."""

from __future__ import annotations

import hashlib
import heapq
import json
import re
import shutil
import sqlite3
from collections.abc import Iterator
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Literal
from uuid import uuid4

import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]

from app.persistence.market import (
    clear_market_symbol,
    delete_market_symbol,
    open_definition_catalog,
    open_market_catalog,
    read_broker_profiles,
)

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


@dataclass(frozen=True)
class MarketDataset:
    """A registered market definition, separate from downloaded coverage."""

    id: str
    source: str
    symbol: str
    kind: Kind
    instrument: str
    broker: str
    timezone: str


@dataclass(frozen=True)
class MarketBroker:
    """Read-only eligible broker profile from the unified catalog."""

    id: str
    name: str
    postfix: str
    timezone: str


@dataclass(frozen=True)
class DefinitionRequest:
    """One immutable provider identity and its user-facing definition."""

    symbol: str
    kind: Kind
    broker: str = "-1"
    postfix: str = ""
    instrument: str = "-1"


class MarketDataStore:
    """Publish and read validated current files under an injected data root."""

    def __init__(self, data_root: Path, database_path: Path) -> None:
        self.data_root = data_root
        self.database_path = database_path

    def available(self) -> bool:
        """Report whether an approved catalog schema already exists."""
        try:
            connection = open_market_catalog(self.database_path)
        except ValueError:
            return False
        connection.close()
        return True

    def list_brokers(self) -> tuple[MarketBroker, ...]:
        """List eligible profiles independently of market-file migration."""
        return tuple(
            MarketBroker(str(broker_id), name, postfix, timezone)
            for broker_id, name, postfix, timezone in read_broker_profiles(
                self.database_path
            )
        )

    def definitions_available(self) -> bool:
        """Check definition storage independently of acquisition storage."""
        try:
            with closing(open_definition_catalog(self.database_path)):
                return True
        except ValueError, sqlite3.Error:
            return False

    def register_definitions(
        self, requests: tuple[DefinitionRequest, ...]
    ) -> tuple[MarketDataset, ...]:
        """Insert a bounded batch atomically, retaining provider identity."""
        if not 1 <= len(requests) <= MAX_DEFINITION_BATCH:
            raise ValueError("Choose between one and 725 symbols")
        brokers = (
            {row.id: row for row in self.list_brokers()}
            if any(row.broker != "-1" for row in requests)
            else {}
        )
        datasets: list[MarketDataset] = []
        now = datetime.now(UTC).isoformat()
        with (
            closing(open_definition_catalog(self.database_path)) as connection,
            connection,
        ):
            connection.execute("BEGIN IMMEDIATE")
            for request in requests:
                if (
                    not re.fullmatch(r"[A-Z0-9_]{2,40}", request.symbol)
                    or request.kind not in ("ticks", "m1")
                    or not re.fullmatch(r"[A-Za-z0-9_.-]{0,40}", request.postfix)
                    or request.instrument not in ("-1", request.symbol)
                    or (request.broker != "-1" and request.broker not in brokers)
                ):
                    raise ValueError(
                        "Invalid symbol, broker, postfix or instrument mapping"
                    )
                name = request.symbol + request.postfix
                timeframe = "M1" if request.kind == "m1" else "TICK"
                if connection.execute(
                    "SELECT 1 FROM datamgr_datasets WHERE source=? AND symbol=? "
                    "AND timeframe=? AND broker=?",
                    ("Dukascopy", name, timeframe, request.broker),
                ).fetchone():
                    raise ValueError("Dukascopy dataset definition already exists")
                dataset = MarketDataset(
                    uuid4().hex,
                    "dukascopy",
                    request.symbol.lower(),
                    request.kind,
                    request.symbol,
                    request.broker,
                    "UTC",
                )
                connection.execute(
                    "INSERT INTO datamgr_datasets "
                    "(id,source,symbol,underlying,instrument,timeframe,broker,broker_name,"
                    "timezone,category,date_from,date_to,bars,created_at,updated_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        dataset.id,
                        "Dukascopy",
                        name,
                        request.symbol,
                        request.symbol,
                        timeframe,
                        request.broker,
                        "Default"
                        if request.broker == "-1"
                        else brokers[request.broker].name,
                        "UTC",
                        "",
                        "",
                        "",
                        0,
                        now,
                        now,
                    ),
                )
                datasets.append(dataset)
        return tuple(datasets)

    def register_dataset(
        self,
        *,
        source: str,
        symbol: str,
        kind: Kind,
        instrument: str,
        broker: str = "-1",
        timezone: str = "UTC",
    ) -> MarketDataset:
        """Register a definition in the pre-existing Data Manager table."""
        self.path(source, kind, symbol, "2000" if kind == "m1" else "2000-01")
        if (
            not instrument
            or len(instrument) > MAX_DATASET_LABEL
            or not broker
            or len(broker) > MAX_DATASET_LABEL
        ):
            raise ValueError("Invalid dataset instrument or broker")
        if timezone != "UTC":
            raise ValueError("Canonical Dukascopy datasets must use UTC")
        dataset = MarketDataset(
            uuid4().hex, source, symbol, kind, instrument, broker, timezone
        )
        now = datetime.now(UTC).isoformat()
        timeframe = "M1" if kind == "m1" else "TICK"
        with closing(open_market_catalog(self.database_path)) as connection, connection:
            existing = connection.execute(
                "SELECT id FROM datamgr_datasets WHERE source=? AND symbol=? "
                "AND timeframe=? AND broker=? AND instrument=?",
                ("Dukascopy", symbol.upper(), timeframe, broker, instrument),
            ).fetchone()
            if existing is not None:
                raise ValueError("Dukascopy dataset definition already exists")
            connection.execute(
                "INSERT INTO datamgr_datasets "
                "(id,source,symbol,underlying,instrument,timeframe,broker,broker_name,"
                "timezone,category,date_from,date_to,bars,created_at,updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    dataset.id,
                    "Dukascopy",
                    symbol.upper(),
                    symbol.upper(),
                    instrument,
                    timeframe,
                    broker,
                    "Default" if broker == "-1" else broker,
                    timezone,
                    "Forex",
                    "",
                    "",
                    0,
                    now,
                    now,
                ),
            )
        return dataset

    def get_dataset(self, dataset_id: str) -> MarketDataset:
        """Resolve a Data Manager ID to a checked Dukascopy source definition."""
        if not re.fullmatch(r"[0-9a-f]{32}", dataset_id):
            raise ValueError("Invalid dataset ID")
        with closing(open_definition_catalog(self.database_path)) as connection:
            row = connection.execute(
                "SELECT id,source,symbol,underlying,instrument,timeframe,"
                "broker,timezone "
                "FROM datamgr_datasets WHERE id=?",
                (dataset_id,),
            ).fetchone()
        if row is None or row["source"] != "Dukascopy":
            raise ValueError("Dukascopy dataset unavailable")
        kind: Kind = "m1" if row["timeframe"] == "M1" else "ticks"
        if row["timeframe"] not in ("M1", "TICK"):
            raise ValueError("Unsupported Dukascopy dataset kind")
        symbol = (row["underlying"] or row["symbol"]).lower()
        self.path("dukascopy", kind, symbol, "2000" if kind == "m1" else "2000-01")
        return MarketDataset(
            row["id"],
            "dukascopy",
            symbol,
            kind,
            row["instrument"],
            row["broker"],
            row["timezone"],
        )

    def list_datasets(self, source: str) -> tuple[dict[str, Any], ...]:
        """List definitions with coverage from committed files only."""
        if source != "dukascopy":
            raise ValueError("Unsupported market source")
        with closing(open_definition_catalog(self.database_path)) as connection:
            rows = connection.execute(
                "SELECT id,symbol,underlying,instrument,timeframe,broker,broker_name,"
                "timezone,category "
                "FROM datamgr_datasets WHERE source=? ORDER BY symbol,id",
                ("Dukascopy",),
            ).fetchall()
        file_stats: dict[tuple[str, str], tuple[int | None, int | None, int]] = {}
        if self.available():
            with closing(open_market_catalog(self.database_path)) as m_conn:
                f_rows = m_conn.execute(
                    "SELECT kind, lower(symbol), min(first_ms), max(last_ms), "
                    "sum(row_count) FROM market_files WHERE source=? "
                    "GROUP BY kind, lower(symbol)",
                    (source,),
                ).fetchall()
                for f_kind, f_sym, f_first, f_last, f_bars in f_rows:
                    file_stats[(f_kind, f_sym)] = (f_first, f_last, f_bars or 0)
        result: list[dict[str, Any]] = []
        for row in rows:
            kind: Kind = "m1" if row["timeframe"] == "M1" else "ticks"
            if row["timeframe"] not in ("M1", "TICK"):
                continue
            sym_key = (kind, (row["underlying"] or row["symbol"]).lower())
            stat = file_stats.get(sym_key)
            first = stat[0] if stat else None
            last = stat[1] if stat else None
            bars = stat[2] if stat else 0
            result.append(
                {
                    "id": row["id"],
                    "symbol": row["symbol"],
                    "source": "Dukascopy",
                    "underlying": row["underlying"] or row["symbol"],
                    "instrument": row["instrument"],
                    "timeframe": row["timeframe"],
                    "broker": row["broker"],
                    "brokerName": row["broker_name"],
                    "timezone": row["timezone"],
                    "category": row["category"],
                    "from": datetime.fromtimestamp(first / 1000, tz=UTC)
                    .date()
                    .isoformat()
                    if first is not None
                    else "",
                    "to": datetime.fromtimestamp(last / 1000, tz=UTC).date().isoformat()
                    if last is not None
                    else "",
                    "bars": bars,
                }
            )
        return tuple(result)

    def delete_dataset(self, symbol: str) -> bool:
        """Purge market files and delete dataset definition."""
        return delete_market_symbol(self.database_path, self.data_root, symbol)

    def clear_dataset(self, symbol: str) -> bool:
        """Purge market files and reset coverage, retaining dataset definition."""
        return clear_market_symbol(self.database_path, self.data_root, symbol)

    def path(self, source: str, kind: Kind, symbol: str, period: str) -> Path:
        """Construct one canonical relative path from checked components."""
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
        path = self.data_root / relative
        if any(
            item.is_symlink() or item.is_junction() for item in (path, *path.parents)
        ):
            raise ValueError("Linked market path")
        return path

    def list_files(
        self, source: str, kind: Kind, symbol: str
    ) -> tuple[MarketFile, ...]:
        """List only committed catalog entries in period order."""
        self.path(source, kind, symbol, "2000" if kind == "m1" else "2000-01")
        with closing(open_market_catalog(self.database_path)) as connection:
            rows = connection.execute(
                "SELECT * FROM market_files WHERE source=? AND kind=? AND symbol=? "
                "ORDER BY period",
                (source, kind, symbol),
            ).fetchall()
        return tuple(self._file(row) for row in rows)

    @staticmethod
    def _file(row: Any) -> MarketFile:
        """Build an immutable descriptor from a checked catalog row."""
        return MarketFile(
            source=row["source"],
            kind=row["kind"],
            symbol=row["symbol"],
            period=row["period"],
            relative_path=row["relative_path"],
            revision=row["revision"],
            sha256=row["sha256"],
            byte_size=row["byte_size"],
            row_count=row["row_count"],
            first_ms=row["first_ms"],
            last_ms=row["last_ms"],
            coverage=tuple(tuple(item) for item in json.loads(row["coverage_json"])),
            provider_mode=row["provider_mode"],
        )

    def _verified_path(self, record: MarketFile) -> Path:
        """Resolve and digest-check one catalog entry before handing it to readers."""
        path = self.path(record.source, record.kind, record.symbol, record.period)
        if path.relative_to(self.data_root).as_posix() != record.relative_path:
            raise ValueError("Market catalog path mismatch")
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        if digest.hexdigest() != record.sha256:
            raise ValueError("Market file digest mismatch")
        return path

    def lazy_scan(self, record: MarketFile) -> Any:
        """Expose a Polars lazy scan of a verified committed file."""
        import polars as pl

        return pl.scan_parquet(self._verified_path(record))

    def query(self, record: MarketFile, sql: str) -> list[tuple[Any, ...]]:
        """Query one verified file as `market_data` in an ephemeral DuckDB view."""
        import duckdb

        path = self._verified_path(record)
        with duckdb.connect(":memory:") as connection:
            connection.read_parquet(str(path)).create_view("market_data")
            return connection.execute(sql).fetchall()

    def publish(
        self,
        *,
        source: str,
        kind: Kind,
        symbol: str,
        period: str,
        table: pa.Table,
        coverage: tuple[tuple[int, int], ...],
        provider_mode: str,
    ) -> MarketFile:
        """Write a validated period, retaining a snapshot of prior revisions."""
        path = self.path(source, kind, symbol, period)
        expected = TICK_SCHEMA if kind == "ticks" else M1_SCHEMA
        if not table.schema.equals(expected) or table.num_rows == 0:
            raise ValueError("Market table schema or row count is invalid")
        stamps = table.column("DateTime").cast(pa.int64()).to_pylist()
        if stamps != sorted(stamps):
            raise ValueError("Market timestamps are not ordered")
        if kind == "m1" and len(set(stamps)) != len(stamps):
            raise ValueError("Duplicate M1 timestamps")
        for stamp in (stamps[0], stamps[-1]):
            instant = datetime.fromtimestamp(stamp / 1000, tz=UTC)
            actual = (
                f"{instant.year:04d}"
                if kind == "m1"
                else f"{instant.year:04d}-{instant.month:02d}"
            )
            if actual != period:
                raise ValueError("Market row lies outside its period")
        if not coverage or any(start > end for start, end in coverage):
            raise ValueError("Invalid covered intervals")
        path.parent.mkdir(parents=True, exist_ok=True)
        previous = next(
            (
                item
                for item in self.list_files(source, kind, symbol)
                if item.period == period
            ),
            None,
        )
        with NamedTemporaryFile(
            dir=path.parent, suffix=".parquet.tmp", delete=False
        ) as stream:
            staged = Path(stream.name)
        try:
            pq.write_table(table, staged, compression="zstd", compression_level=6)
            metadata = pq.read_metadata(staged)
            if (
                metadata.num_rows != table.num_rows
                or metadata.schema.to_arrow_schema() != expected
            ):
                raise ValueError("Staged Parquet verification failed")
            data = staged.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            revision = previous.revision + 1 if previous else 1
            if previous:
                self._verified_path(previous)
                revisions = self.data_root / "market-revisions" / source / kind / symbol
                revisions.mkdir(parents=True, exist_ok=True)
                snapshot = revisions / f"{period}-{previous.revision}.parquet"
                if snapshot.exists():
                    raise ValueError("Prior revision already archived")
                snapshot.write_bytes(path.read_bytes())
            Path(staged).replace(path)
            now = datetime.now(UTC).isoformat()
            relative = path.relative_to(self.data_root).as_posix()
            with (
                closing(open_market_catalog(self.database_path)) as connection,
                connection,
            ):
                connection.execute(
                    "INSERT OR REPLACE INTO market_files "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        source,
                        kind,
                        symbol,
                        period,
                        relative,
                        revision,
                        digest,
                        len(data),
                        table.num_rows,
                        stamps[0],
                        stamps[-1],
                        json.dumps(coverage),
                        provider_mode,
                        now,
                    ),
                )
            return MarketFile(
                source,
                kind,
                symbol,
                period,
                relative,
                revision,
                digest,
                len(data),
                table.num_rows,
                stamps[0],
                stamps[-1],
                coverage,
                provider_mode,
            )
        finally:
            staged.unlink(missing_ok=True)

    def replace_interval(  # noqa: C901, PLR0912, PLR0915 -- bounded merge and commit stay auditable.
        self,
        *,
        source: str,
        kind: Kind,
        symbol: str,
        period: str,
        incoming: pa.Table,
        start_ms: int,
        end_ms: int,
        provider_mode: str,
    ) -> MarketFile:
        """Replace one interval by streaming an immutable period rewrite."""
        path = self.path(source, kind, symbol, period)
        schema = TICK_SCHEMA if kind == "ticks" else M1_SCHEMA
        if not incoming.schema.equals(schema) or start_ms > end_ms:
            raise ValueError("Invalid market interval")

        def stamp(row: dict[str, Any]) -> int:
            return int(row["DateTime"].timestamp() * 1000)

        fresh: list[dict[str, Any]] = incoming.to_pylist()
        if any(not start_ms <= stamp(row) <= end_ms for row in fresh):
            raise ValueError("Incoming market row outside requested interval")
        if fresh != sorted(fresh, key=stamp):
            raise ValueError("Incoming market rows are unordered")
        if kind == "m1" and len({stamp(row) for row in fresh}) != len(fresh):
            raise ValueError("Duplicate M1 timestamps")
        previous = next(
            (
                item
                for item in self.list_files(source, kind, symbol)
                if item.period == period
            ),
            None,
        )

        def retained() -> Iterator[dict[str, Any]]:
            if previous is None:
                return
            parquet = pq.ParquetFile(self._verified_path(previous))
            if not parquet.schema_arrow.equals(schema):
                raise ValueError("Prior market schema mismatch")
            for batch in parquet.iter_batches(batch_size=BATCH_ROWS):
                for row in batch.to_pylist():
                    if not start_ms <= stamp(row) <= end_ms:
                        yield row

        staging = self.data_root / "market-staging"
        staging.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=staging, suffix=".parquet", delete=False) as stream:
            staged = Path(stream.name)
        count = first_ms = last_ms = 0
        try:
            merged = heapq.merge(retained(), fresh, key=stamp)
            buffered: list[dict[str, Any]] = []

            def append_row(row: dict[str, Any], writer: pq.ParquetWriter) -> None:
                nonlocal count, first_ms, last_ms
                current = stamp(row)
                instant = datetime.fromtimestamp(current / 1000, tz=UTC)
                actual = (
                    f"{instant.year:04d}"
                    if kind == "m1"
                    else f"{instant.year:04d}-{instant.month:02d}"
                )
                if actual != period:
                    raise ValueError("Market row lies outside period")
                if count == 0:
                    first_ms = current
                last_ms = current
                count += 1
                buffered.append(row)
                if len(buffered) >= BATCH_ROWS:
                    writer.write_table(pa.Table.from_pylist(buffered, schema=schema))
                    buffered.clear()

            with pq.ParquetWriter(
                staged, schema, compression="zstd", compression_level=6
            ) as writer:
                pending: dict[str, Any] | None = None
                for row in merged:
                    if kind == "ticks":
                        append_row(row, writer)
                        continue
                    if pending is not None and stamp(row) != stamp(pending):
                        append_row(pending, writer)
                    pending = row
                if pending is not None:
                    append_row(pending, writer)
                if buffered:
                    writer.write_table(pa.Table.from_pylist(buffered, schema=schema))
            if count == 0:
                raise ValueError("No market rows to publish")
            metadata = pq.read_metadata(staged)
            if (
                metadata.num_rows != count
                or not metadata.schema.to_arrow_schema().equals(schema)
            ):
                raise ValueError("Staged market file verification failed")
            digest = hashlib.sha256()
            with staged.open("rb") as staged_file:
                for block in iter(lambda: staged_file.read(1024 * 1024), b""):
                    digest.update(block)
            revision = previous.revision + 1 if previous else 1
            if previous:
                revisions = self.data_root / "market-revisions" / source / kind / symbol
                revisions.mkdir(parents=True, exist_ok=True)
                snapshot = revisions / f"{period}-{previous.revision}.parquet"
                with path.open("rb") as old_file, snapshot.open("xb") as saved_file:
                    shutil.copyfileobj(old_file, saved_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            staged.replace(path)
            coverage = (
                tuple(sorted((*previous.coverage, (start_ms, end_ms))))
                if previous
                else ((start_ms, end_ms),)
            )
            relative = path.relative_to(self.data_root).as_posix()
            size = path.stat().st_size
            digest_hex = digest.hexdigest()
            with (
                closing(open_market_catalog(self.database_path)) as connection,
                connection,
            ):
                connection.execute(
                    "INSERT OR REPLACE INTO market_files "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        source,
                        kind,
                        symbol,
                        period,
                        relative,
                        revision,
                        digest_hex,
                        size,
                        count,
                        first_ms,
                        last_ms,
                        json.dumps(coverage),
                        provider_mode,
                        datetime.now(UTC).isoformat(),
                    ),
                )
            return MarketFile(
                source,
                kind,
                symbol,
                period,
                relative,
                revision,
                digest_hex,
                size,
                count,
                first_ms,
                last_ms,
                coverage,
                provider_mode,
            )
        finally:
            staged.unlink(missing_ok=True)
