"""Source-bound differential and exhausted-transport regression qualification."""

from __future__ import annotations

import ast
import asyncio
import hashlib
import json
import logging
import lzma
import os
import struct
import typing
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]
import pytest
from app.cli import Client
from app.host.capabilities import NetworkAccess
from app.host.network import HistoricalNetwork, NetworkResult, NetworkUnavailableError
from app.persistence.market import (
    M1_SCHEMA,
    TICK_SCHEMA,
    MarketDataset,
    MarketDataStore,
    create_isolated_schema,
)
from app.plugin.DataSource.dukascopy import (
    SYMBOL_DETAILS,
    _dataframe_to_canonical_m1,
    _dataframe_to_canonical_ticks,
    _decode_m1,
    _decode_ticks,
    _fetch_day_result,
    _get_symbol_info,
    _parse_datetime,
    _spec,
)


@pytest.fixture
def reference() -> dict[str, Any]:
    """Compile only selected owner functions; never execute source module startup."""
    path = Path(
        os.environ.get("HARU_DUKASCOPY_REFERENCE", "C:/SQX/scripts/dukascopy.py")
    )
    if not path.is_file():
        pytest.skip("Owner reference unavailable; source-bound parity is unqualified")
    source = path.read_bytes()
    assert (
        hashlib.sha256(source).hexdigest().upper()
        == "2F43019B97DD735E24E35F6F77A9EF0F2520A2E057ED24C9C8C9F8DBF701F298"  # pragma: allowlist secret -- reference-source SHA256, not a credential.
    )
    parsed = ast.parse(source.decode("utf-8"))
    names = {
        "_SymbolInfo",
        "_load_sqx_csv_catalog",
        "_get_symbol_info",
        "_decompress_bi5",
        "_fetch_m1_day_direct",
        "_fetch_tick_hour_direct",
        "_parse_datetime",
        "_dataframe_to_canonical_m1",
        "_dataframe_to_canonical_ticks",
        "_store_canonical_partitions",
        "_resolve_market_partition_path",
        "_scan_market_m1",
        "_scan_market_ticks",
        "add_symbol",
    }
    nodes: list[ast.stmt] = [
        node
        for node in parsed.body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names
    ]
    nodes.insert(
        0,
        ast.ImportFrom(
            module="__future__", names=[ast.alias(name="annotations")], level=0
        ),
    )
    env: dict[str, Any] = {
        **vars(typing),
        "np": np,
        "pd": pd,
        "pa": pa,
        "pq": pq,
        "Path": Path,
        "dataclass": dataclass,
        "datetime": datetime,
        "date": date,
        "timezone": __import__("datetime").timezone,
        "timedelta": __import__("datetime").timedelta,
        "struct": struct,
        "lzma": lzma,
        "logger": logging.getLogger("reference"),
        "re": __import__("re"),
        "os": os,
        "time": __import__("time"),
        "sqlite3": __import__("sqlite3"),
        "__file__": str(path),
        "KNOWN_SYMBOLS": {},
        "DUKASCOPY_FEED_HTTPS": "https://datafeed.dukascopy.com/datafeed",
        "M1_SCHEMA": M1_SCHEMA,
        "TICK_SCHEMA": TICK_SCHEMA,
    }
    for node in parsed.body:
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "KNOWN_SYMBOLS"
            and node.value is not None
        ):
            env["KNOWN_SYMBOLS"] = ast.literal_eval(node.value)
    exec(
        compile(
            ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])),
            str(path),
            "exec",
        ),
        env,
    )
    env["SYMBOL_METADATA"] = {**env["KNOWN_SYMBOLS"], **env["_load_sqx_csv_catalog"]()}
    env["_get_symbol_info"] = env["_get_symbol_info"]
    env["CANDLE_DTYPE"] = np.dtype(
        [
            ("offset_sec", ">i4"),
            ("open", ">i4"),
            ("close", ">i4"),
            ("low", ">i4"),
            ("high", ">i4"),
            ("vol", ">f4"),
        ]
    )
    env["TICK_DTYPE"] = np.dtype(
        [
            ("offset_ms", ">i4"),
            ("ask", ">i4"),
            ("bid", ">i4"),
            ("ask_vol", ">f4"),
            ("bid_vol", ">f4"),
        ]
    )
    return env


def test_complete_catalog_matches_owner(reference: dict[str, Any]) -> None:
    """Every owner catalog entry and heuristic resolves the same price metadata."""
    assert len(SYMBOL_DETAILS) > 1300
    for symbol in (
        *reference["SYMBOL_METADATA"],
        "NAS100NEW",
        "UNKNOWN",
        "FOOJPY",
        "BTCNEW",
        "OILNEW",
    ):
        actual, expected = (
            _get_symbol_info(symbol),
            reference["_get_symbol_info"](symbol),
        )
        assert (
            actual.decimals,
            actual.point_size,
            actual.category,
            actual.m1_start,
            actual.tick_start,
            actual.pip_size,
        ) == (
            expected.decimals,
            expected.point_size,
            expected.category,
            expected.m1_start,
            expected.tick_start,
            expected.pip_size,
        ), symbol


@pytest.mark.parametrize("symbol", ["EURUSD", "CADJPY", "XAUUSD", "BTCUSD"])
def test_numeric_source_pipeline(reference: dict[str, Any], symbol: str) -> None:
    """Compare original direct decoding and canonical conversion on identical bytes."""
    instant = datetime(2024, 1, 15, tzinfo=UTC)
    m1 = lzma.compress(
        struct.pack(">IIIIIf", 60, 110012, 110019, 110000, 110050, 0.123456),
        format=lzma.FORMAT_ALONE,
    )
    ticks = lzma.compress(
        struct.pack(">IIIff", 100, 110019, 110012, 0.123456, 0.456789),
        format=lzma.FORMAT_ALONE,
    )

    class Fixture:
        def get(self, url: str) -> bytes:
            return ticks if "ticks" in url else m1

    reference["_NETWORK"] = Fixture()
    decimals = _get_symbol_info(symbol).decimals
    frame = reference["_fetch_m1_day_direct"](symbol, instant.date(), decimals)
    expected = reference["_dataframe_to_canonical_m1"](frame)
    assert _dataframe_to_canonical_m1(frame).equals(expected)
    assert _decode_m1(m1, instant, symbol)[0][1:] == tuple(
        expected.to_pylist()[0][key]
        for key in ("Open", "High", "Low", "Close", "Volume")
    )
    arrays = reference["_fetch_tick_hour_direct"](symbol, instant, decimals)
    tick_frame = pd.DataFrame(
        dict(
            zip(
                ("timestamp", "ask", "bid", "ask_volume", "bid_volume"),
                arrays,
                strict=True,
            )
        )
    )
    tick_frame["timestamp"] = pd.to_datetime(
        tick_frame["timestamp"], unit="ms", utc=True
    )
    expected_ticks = reference["_dataframe_to_canonical_ticks"](tick_frame)
    assert _dataframe_to_canonical_ticks(tick_frame).equals(expected_ticks)
    assert _decode_ticks(ticks, instant, symbol)[0][0] == int(
        expected_ticks.to_pylist()[0]["DateTime"].timestamp() * 1000
    )
    assert _decode_ticks(ticks, instant, symbol)[0][1:] == tuple(
        expected_ticks.to_pylist()[0][key] for key in ("Ask", "Bid", "Volume")
    )


def test_logged_timeout_sequence_falls_back_to_http(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """503 plus two HTTPS timeouts must recover using HTTP, not kill the job."""
    contacts: list[str] = []
    payload = lzma.compress(
        struct.pack(">IIIIIf", 60, 110000, 110010, 109990, 110020, 0.05),
        format=lzma.FORMAT_ALONE,
    )

    async def no_wait(seconds: float) -> None:
        return None

    monkeypatch.setattr("app.host.network.asyncio.sleep", no_wait)

    def respond(request: httpx.Request) -> httpx.Response:
        contacts.append(str(request.url))
        if request.url.scheme == "http":
            return httpx.Response(200, content=payload)
        if len(contacts) == 1:
            return httpx.Response(503)
        raise httpx.ConnectTimeout("fixture", request=request)

    async def scenario() -> None:
        network = HistoricalNetwork(
            httpx.AsyncClient(transport=httpx.MockTransport(respond))
        )
        dataset = MarketDataset(
            "id", "dukascopy", "cadjpy", "m1", "CADJPY", "-1", "UTC"
        )
        result = await _fetch_day_result(
            NetworkAccess("plugin.data_manager.dukascopy", network),
            dataset,
            date(2026, 9, 30),
        )
        assert result.table.num_rows == 1
        assert result.failed_chunks == 0
        assert len(result.received_intervals) == 1
        await network.aclose()

    asyncio.run(scenario())
    assert len(contacts) == 4
    assert contacts[-1].startswith("http://")
    assert "/2026/08/30/" in contacts[-1]


def test_direct_source_arrays_preserve_raw_side_volumes(
    reference: dict[str, Any],
) -> None:
    """Direct raw adapters agree before canonical combined-volume custody."""
    from app.plugin.DataSource.dukascopy import (
        _fetch_m1_day_direct,
        _fetch_tick_hour_direct,
    )

    instant = datetime(2024, 1, 15, tzinfo=UTC)
    m1 = lzma.compress(
        struct.pack(">IIIIIf", 60, 110012, 110019, 110000, 110050, 0.00000234),
        format=lzma.FORMAT_ALONE,
    )
    ticks = lzma.compress(
        struct.pack(">IIIff", 100, 110019, 110012, 0.01, 0.02), format=lzma.FORMAT_ALONE
    )

    class OriginalFixture:
        def get(self, url: str) -> bytes:
            return ticks if "ticks" in url else m1

    class HostFixture(HistoricalNetwork):
        async def get(self, url: str) -> NetworkResult:
            return NetworkResult(200, ticks if "ticks" in url else m1)

    reference["_NETWORK"] = OriginalFixture()
    access = NetworkAccess("plugin.data_manager.dukascopy", HostFixture())
    actual_m1 = asyncio.run(_fetch_m1_day_direct(access, "EURUSD", instant.date(), 5))
    expected_m1 = reference["_fetch_m1_day_direct"]("EURUSD", instant.date(), 5)
    pd.testing.assert_frame_equal(actual_m1, expected_m1)
    actual_ticks = asyncio.run(_fetch_tick_hour_direct(access, "EURUSD", instant, 5))
    expected_ticks = reference["_fetch_tick_hour_direct"]("EURUSD", instant, 5)
    assert actual_ticks is not None
    for actual, expected in zip(actual_ticks, expected_ticks, strict=True):
        np.testing.assert_array_equal(actual, expected)


def test_failed_hour_retains_received_rows_and_precise_coverage() -> None:
    """Unavailable or corrupt hours cannot acquire coverage or erase valid rows."""
    payload = lzma.compress(
        struct.pack(">IIIff", 100, 110019, 110012, 0.01, 0.02), format=lzma.FORMAT_ALONE
    )

    class Fixture(HistoricalNetwork):
        async def get(self, url: str) -> NetworkResult:
            if "/00h_" in url:
                raise NetworkUnavailableError("fixture transport exhausted")
            if "/01h_" in url:
                return NetworkResult(200, b"broken")
            return (
                NetworkResult(200, payload)
                if "/02h_" in url
                else NetworkResult(404, b"")
            )

    dataset = MarketDataset("id", "dukascopy", "cadjpy", "ticks", "CADJPY", "-1", "UTC")
    result = asyncio.run(
        _fetch_day_result(
            NetworkAccess("plugin.data_manager.dukascopy", Fixture()),
            dataset,
            date(2026, 9, 30),
        )
    )
    assert result.table.num_rows == 1
    assert result.failed_chunks == 2
    assert result.missing_chunks == 21
    assert result.received_intervals == (
        (1790726400000 + 7200000, 1790726400000 + 10800000 - 1),
    )


def test_multiyear_and_time_boundaries(reference: dict[str, Any]) -> None:
    """The backend accepts UI multi-year ranges and source minute boundary semantics."""
    spec = _spec(
        {"dataset_id": "id", "date_from": "2010-01-01", "date_to": "2020-01-01"}
    )
    assert (spec.last - spec.first).days > 366
    for value in (
        "2020-01-01",
        "2020-01-01 12:30",
        "2020-01-01T12:30:00+02:00",
        datetime(2020, 1, 1, tzinfo=UTC),
    ):
        for is_end in (False, True):
            assert _parse_datetime(value, is_end) == reference["_parse_datetime"](
                value, is_end
            )
    with pytest.raises(ValueError):
        _spec(
            {
                "dataset_id": "id",
                "date_from": "2020-01-01",
                "date_to": "2020-02-01",
                "workers": 0,
            }
        )


def test_source_timestamp_merge_preserves_unresent_rows(tmp_path: Path) -> None:
    """Source OVERWRITE replaces matching timestamps rather than deleting a day."""
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)
    dataset = store.register_dataset(
        source="dukascopy", symbol="eurusd", kind="m1", instrument="EURUSD"
    )

    def table(seconds: list[int], price: float) -> Any:
        return pa.Table.from_pylist(
            [
                {
                    "DateTime": datetime(2020, 1, 1, 0, minute, tzinfo=UTC),
                    "Open": price,
                    "High": price,
                    "Low": price,
                    "Close": price,
                    "Volume": 1,
                }
                for minute in seconds
            ],
            schema=M1_SCHEMA,
        )

    first = 1577836800000
    for incoming in (table([0, 1], 1.0), table([0], 2.0)):
        store.replace_interval(
            source="dukascopy",
            kind="m1",
            symbol="eurusd",
            period="2020",
            incoming=incoming,
            start_ms=first,
            end_ms=first + 86400000 - 1,
            provider_mode="standard",
            merge_timestamps=True,
        )
    rows = store.read_market_rows(
        dataset.id, start_ms=first, end_ms=first + 86400000 - 1
    ).to_pylist()
    assert [row["Close"] for row in rows] == [2.0, 1.0]


@pytest.mark.parametrize("kind", ["m1", "ticks"])
def test_job_raw_results_and_canonical_storage(  # noqa: C901, PLR0915 -- complete custody lifecycle.
    tmp_path: Path,
    kind: str,
    reference: dict[str, Any],
) -> None:
    """Raw resources retain source precision; stored-only results identify custody."""
    from app.host.capabilities import (
        HostCapabilities,
        JobAccess,
        MarketAccess,
        ResourceAccess,
    )
    from app.host.jobs import JobManager
    from app.persistence.resources import ResourceStore
    from app.plugin.DataSource import dukascopy

    instant = datetime(2024, 1, 15, tzinfo=UTC)
    payload = lzma.compress(
        struct.pack(">IIIIIf", 60, 110000, 110010, 109990, 110020, 0.00000234)
        if kind == "m1"
        else struct.pack(">IIIff", 17, 110002, 110000, 0.00000123, 0.00000234),
        format=lzma.FORMAT_ALONE,
    )
    create_isolated_schema(tmp_path / "market.db")
    resource_store = ResourceStore(tmp_path / "resources")
    owner = "plugin.data_manager.dukascopy"

    class Feed(HistoricalNetwork):
        async def get(self, url: str) -> NetworkResult:
            return NetworkResult(200, payload)

    async def scenario() -> None:  # noqa: PLR0915 -- complete custody lifecycle.
        manager = JobManager(1, 256 * 1024 * 1024)
        market = MarketAccess(
            owner, MarketDataStore(tmp_path / "market", tmp_path / "market.db")
        )
        feed = Feed()
        caps = HostCapabilities(
            resources=ResourceAccess(owner, "1.0.0", resource_store),
            jobs=JobAccess(owner, manager),
            market_data=market,
            network=NetworkAccess(owner, feed),
            log=None,
        )
        contribution = await dukascopy._prepare(caps)
        dataset = market.register_dataset(
            "eurusd", "m1" if kind == "m1" else "ticks", "EURUSD"
        )

        async def acquire(
            overwrite: bool,
            end: str | None = None,
        ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
            started = typing.cast(
                "dict[str, Any]",
                await contribution.invoke(
                    "download.start",
                    {
                        "dataset_id": dataset.id,
                        "date_from": instant.isoformat(),
                        "date_to": end
                        or ("2024-01-15" if kind == "m1" else "2024-01-15T00:59"),
                        "overwrite": overwrite,
                        "result_representation": "provider",
                        "workers": 1,
                    },
                ),
            )
            await asyncio.wait_for(manager.tasks[started["job_id"]], timeout=5)
            status = typing.cast(
                "dict[str, Any]",
                await contribution.invoke(
                    "download.status", {"job_id": started["job_id"]}
                ),
            )
            assert status["state"] == "succeeded", status
            pages: list[dict[str, Any]] = []
            offset = 0
            while True:
                page = typing.cast(
                    "dict[str, Any]",
                    await contribution.invoke(
                        "download.results.read",
                        {"job_id": started["job_id"], "offset": offset, "limit": 1},
                    ),
                )
                pages.append(page)
                if not page["has_more"]:
                    break
                assert page["next_offset"] > offset
                offset = page["next_offset"]
            return started, pages

        started, pages = await acquire(True)
        assert pages[0]["origin"] == "provider"
        row = pages[0]["rows"][0]
        assert (
            pages[0]["dtypes"]["ask_volume" if kind == "ticks" else "volume"]
            == "float32"
        )
        raw = dukascopy._provider_table(payload, instant, "EURUSD", kind).to_pandas()
        if kind == "m1":
            expected = reference["_fetch_m1_day_direct"]

            class Response:
                status_code = 200
                content = payload

            reference["_NETWORK"] = typing.cast(
                "Any",
                type("Requests", (), {"get": staticmethod(lambda *_a, **_k: payload)}),
            )
            donor = expected("EURUSD", instant.date(), 5)
            np.testing.assert_array_equal(raw["volume"].values, donor["volume"].values)
            assert row["volume"] == float(donor["volume"].iloc[0])
        else:
            assert row["ask_volume"] != row["bid_volume"]
            assert row["ask"] == 1.10002
        canonical = market.read_market_rows(
            dataset.id,
            start_ms=int(instant.timestamp() * 1000),
            end_ms=int(instant.timestamp() * 1000) + 3599999,
        )
        assert canonical.column("Volume").to_pylist() == [2 if kind == "m1" else 4]
        _, stored = await acquire(False)
        assert stored[0]["origin"] == "canonical"
        assert (
            stored[0]["dtypes"]["ask_volume" if kind == "ticks" else "volume"]
            == "uint64"
        )
        if kind == "ticks":
            assert (
                stored[0]["rows"][0]["ask_volume"]
                == stored[0]["rows"][0]["bid_volume"]
                == 4
            )
        else:
            assert stored[0]["rows"][0]["volume"] == 2
        _, mixed = await acquire(
            False,
            "2024-01-16T00:59:59+00:00"
            if kind == "m1"
            else "2024-01-15T01:59:59+00:00",
        )
        assert {page["origin"] for page in mixed} == {"provider", "canonical"}
        pages_by_origin = {page["origin"]: page for page in mixed}
        assert (
            pages_by_origin["provider"]["dtypes"][
                "ask_volume" if kind == "ticks" else "volume"
            ]
            == "float32"
        )
        assert (
            pages_by_origin["canonical"]["dtypes"][
                "ask_volume" if kind == "ticks" else "volume"
            ]
            == "uint64"
        )

        # Provider pages and stored pages may interleave within a day; client sorts
        # within its explicit memory bound before exports or API concatenation.
        class PageClient(Client):
            def request(self, route: str, data: dict[str, Any] | None = None) -> Any:
                return next(
                    page
                    for page in mixed
                    if page["next_offset"] > (data or {})["offset"]
                )

        frames = list(
            dukascopy._result_frames(PageClient("http://localhost:8000"), "job")
        )
        combined = pd.concat(frames, ignore_index=True)
        assert combined["timestamp"].is_monotonic_increasing
        assert len(combined) == 2
        for limit in (0, 2001):
            with pytest.raises(ValueError, match="bounds"):
                await contribution.invoke(
                    "download.results.read",
                    {"job_id": started["job_id"], "limit": limit},
                )
        with pytest.raises(ValueError, match="bounds"):
            await contribution.invoke("download.results.read", {"job_id": "unknown"})
        refs = resource_store.list("reader")
        assert refs and refs[0].producer_id == owner
        with pytest.raises(PermissionError):
            ResourceAccess("intruder", "1.0.0", resource_store).publish(
                b"x",
                schema_id="bad",
                schema_version="1.0.0",
                schema_json="{}",
                media_type="bytes",
                previous=refs[0],
            )
        # Digest and schema reads are generic and continue after producer shutdown.
        await contribution.close()
        await manager.close()
        await feed.aclose()
        for ref in refs:
            content, schema = resource_store.read("independent-reader", ref)
            assert content and json.loads(schema)["dataset_id"] == dataset.id
        record = tmp_path / "resources" / f"{refs[0].id}.1.json"
        document = json.loads(record.read_text())
        document["content_base64"] = "eA=="
        record.write_text(json.dumps(document))
        with pytest.raises(ValueError, match="checksum"):
            resource_store.read("independent-reader", refs[0])

    asyncio.run(scenario())


def test_result_pagination_cancellation_and_missing_capability(tmp_path: Path) -> None:
    """Completed chunks remain readable after cancellation; authority fails closed."""
    from app.host.capabilities import (
        HostCapabilities,
        JobAccess,
        MarketAccess,
        ResourceAccess,
    )
    from app.host.jobs import JobManager
    from app.persistence.resources import ResourceStore
    from app.plugin.DataSource import dukascopy

    owner = "plugin.data_manager.dukascopy"
    create_isolated_schema(tmp_path / "market.db")
    payload = lzma.compress(
        b"".join(
            struct.pack(
                ">IIIIIf", index * 30, 110000, 110010, 109990, 110020, 0.00000234
            )
            for index in range(2001)
        ),
        format=lzma.FORMAT_ALONE,
    )

    async def scenario() -> None:
        blocked = asyncio.Event()
        hold = asyncio.Event()

        class Feed(HistoricalNetwork):
            async def get(self, url: str) -> NetworkResult:
                if "/16/" in url:
                    blocked.set()
                    await hold.wait()
                return NetworkResult(200, payload)

        manager = JobManager(1, 256 * 1024 * 1024)
        feed = Feed()
        market = MarketAccess(
            owner, MarketDataStore(tmp_path / "market", tmp_path / "market.db")
        )
        resource_store = ResourceStore(tmp_path / "resources")
        for resource in (
            None,
            ResourceAccess("other", "1.0.0", resource_store),
            ResourceAccess(owner, "2.0.0", resource_store),
        ):
            with pytest.raises(ValueError, match="resource capability"):
                await dukascopy._prepare(
                    HostCapabilities(
                        resources=resource,
                        jobs=JobAccess(owner, manager),
                        market_data=market,
                        network=NetworkAccess(owner, feed),
                        log=None,
                    )
                )
        contribution = await dukascopy._prepare(
            HostCapabilities(
                resources=ResourceAccess(owner, "1.0.0", resource_store),
                jobs=JobAccess(owner, manager),
                market_data=market,
                network=NetworkAccess(owner, feed),
                log=None,
            )
        )
        dataset = market.register_dataset("eurusd", "m1", "EURUSD")
        started = typing.cast(
            "dict[str, Any]",
            await contribution.invoke(
                "download.start",
                {
                    "dataset_id": dataset.id,
                    "date_from": "2024-01-15",
                    "date_to": "2024-01-16",
                    "workers": 1,
                    "result_representation": "provider",
                },
            ),
        )
        await asyncio.wait_for(blocked.wait(), timeout=5)
        job_id = started["job_id"]
        page = typing.cast(
            "dict[str, Any]",
            await contribution.invoke("download.results.read", {"job_id": job_id}),
        )
        assert (
            len(page["rows"]) == 2000
            and page["has_more"]
            and page["next_offset"] == 2000
        )
        tail = typing.cast(
            "dict[str, Any]",
            await contribution.invoke(
                "download.results.read", {"job_id": job_id, "offset": 2000}
            ),
        )
        assert len(tail["rows"]) == 1 and not tail["has_more"]
        await contribution.invoke("download.cancel", {"job_id": job_id})
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(manager.tasks[job_id], timeout=5)
        status = typing.cast(
            "dict[str, Any]",
            await contribution.invoke("download.status", {"job_id": job_id}),
        )
        assert status["state"] == "cancelled" and status["published_days"] == 1
        assert (
            await contribution.invoke(
                "download.results.read", {"job_id": job_id, "offset": 2000}
            )
            == tail
        )
        refs = resource_store.list("independent")
        assert len(refs) == 1
        # Schema provenance is verified as well as immutable byte identity.
        record = tmp_path / "resources" / f"{refs[0].id}.1.json"
        document = json.loads(record.read_text())
        schema = json.loads(document["schema_document"])
        original_schema = json.loads(json.dumps(schema))
        for key, value, message in (
            ("request_id", "forged", "provenance"),
            ("dataset_id", "forged", "provenance"),
            ("schema_version", "2.0.0", "provenance"),
            ("fields", [], "schema"),
            ("start_ms", 0, "range"),
            ("representation", "canonical", "representation"),
        ):
            changed = {**original_schema, key: value}
            document["schema_document"] = json.dumps(changed)
            record.write_text(json.dumps(document))
            with pytest.raises(ValueError, match=message):
                await contribution.invoke("download.results.read", {"job_id": job_id})
        await contribution.close()
        await manager.close()
        await feed.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "timeframe", ["m1", "m5", "m15", "m30", "h1", "h4", "d1", "w1"]
)
@pytest.mark.parametrize("tz", [None, "Europe/London", "Asia/Kolkata"])
def test_source_scan_resampling_dtype_timezone(
    tmp_path: Path,
    reference: dict[str, Any],
    timeframe: str,
    tz: str | None,
) -> None:
    """Compare complete canonical scan frames, including UTC aggregation boundaries."""
    from app.plugin.DataSource import dukascopy

    times = pd.date_range("2024-03-30T22:17:00Z", periods=600, freq="min")
    frame = pd.DataFrame(
        {
            "DateTime": times,
            "Open": np.arange(600) / 100 + 1,
            "High": np.arange(600) / 100 + 2,
            "Low": np.arange(600) / 100,
            "Close": np.arange(600) / 100 + 1.5,
            "Volume": np.arange(600, dtype=np.uint64),
        }
    )
    table = pa.Table.from_pandas(frame, schema=M1_SCHEMA, preserve_index=False)
    folder = tmp_path / "dukascopy/m1/eurusd"
    folder.mkdir(parents=True)
    pq.write_table(table, folder / "2024.parquet")
    start, end = "2024-03-30 22:20", "2024-03-31 07:00"

    class ScanClient(Client):
        def request(self, route: str, data: dict[str, Any] | None = None) -> Any:
            if route.endswith("catalog"):
                return {
                    "market_root": str(tmp_path.resolve()),
                    "datasets": [
                        {
                            "id": "a" * 32,
                            "underlying": "EURUSD",
                            "symbol": "EURUSD",
                            "timeframe": "M1",
                            "source": "Dukascopy",
                        }
                    ],
                }
            if route.endswith("actions.list_datasets"):
                return [
                    {
                        "id": "a" * 32,
                        "underlying": "EURUSD",
                        "symbol": "EURUSD",
                        "timeframe": "M1",
                        "source": "Dukascopy",
                    }
                ]
            values = data or {}
            filtered = frame[
                (frame["DateTime"] >= dukascopy._parse_datetime(start))
                & (frame["DateTime"] <= dukascopy._parse_datetime(end, True))
            ]
            page = filtered.iloc[
                values["offset"] : values["offset"] + values["limit"]
            ].copy()
            page["DateTime"] = page["DateTime"].map(lambda value: value.isoformat())
            return {
                "rows": page.to_dict("records"),
                "has_more": False,
                "next_offset": len(page),
            }

    donor = reference["_scan_market_m1"](
        "EURUSD",
        timeframe=timeframe,
        start=start,
        end=end,
        store_root=tmp_path,
        source="dukascopy",
        tz=tz,
    )
    actual = dukascopy._scan_market_m1(
        "EURUSD",
        timeframe,
        start,
        end,
        tmp_path,
        tz=tz,
        client=ScanClient("http://localhost:8000"),
    )
    pd.testing.assert_frame_equal(
        actual.reset_index(drop=True), donor.reset_index(drop=True), check_dtype=True
    )
