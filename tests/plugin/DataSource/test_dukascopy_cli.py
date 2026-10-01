"""CLI contract tests against provider-shaped authenticated host responses."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest
from app.cli import Client, ClientError, write_table_output
from app.host.capabilities import (
    HostCapabilities,
    JobAccess,
    MarketAccess,
    NetworkAccess,
    ResourceAccess,
)
from app.host.jobs import JobManager
from app.host.network import HistoricalNetwork
from app.persistence.market import MarketDataStore, create_isolated_schema
from app.persistence.resources import ResourceStore
from app.plugin.DataSource import dukascopy
from pydantic import JsonValue


def test_reference_public_exports_and_internal_host_hook() -> None:
    """Only the three UI actions are user exports; discovery retains its hook."""
    import inspect
    from importlib import import_module

    current = import_module("app.plugin.DataSource.dukascopy")

    expected = ["add_symbol", "download_data", "show_disclaimer"]
    assert current.__all__ == expected
    namespace: dict[str, object] = {}
    exec("from app.plugin.DataSource.dukascopy import *", namespace)
    assert set(namespace) - {"__builtins__"} == set(expected)
    assert all(namespace[name] is getattr(current, name) for name in expected)
    functions = {
        name: value
        for name, value in vars(current).items()
        if inspect.isfunction(value) and value.__module__ == current.__name__
    }
    assert {
        value.__name__
        for value in functions.values()
        if not value.__name__.startswith("_")
    } == set(expected)
    assert {name for name in functions if not name.startswith("_")} == set(expected) | {
        "prepare"
    }
    assert current.prepare is current._prepare
    assert inspect.iscoroutinefunction(current.prepare)
    assert not any(
        hasattr(current, name)
        for name in (
            "main",
            "dashboard",
            "decode_ticks",
            "download_m1",
            "scan_market_m1",
        )
    )


class FixtureClient(Client):
    """A route-recording client whose effects mimic the host's published contracts."""

    def __init__(self, root: Path) -> None:
        super().__init__("http://127.0.0.1:8000")
        self.routes: list[tuple[str, dict[str, Any]]] = []
        self.root = root
        self.datasets: list[dict[str, Any]] = []

    def request(self, route: str, data: dict[str, Any] | None = None) -> Any:  # noqa: PLR0911 -- distinct published host contracts.
        values = data or {}
        self.routes.append((route, values))
        if route.endswith(".catalog"):
            return {
                "definitions_available": True,
                "market_root": str(self.root.resolve()),
                "brokers": [{"id": "3", "name": "Dukascopy", "postfix": "_dukascopy"}],
                "datasets": self.datasets,
            }
        if route.endswith(".definitions.add"):
            key = values["symbols"][0] + ("M1" if values["kind"] == "m1" else "TICK")
            if not any(row["id"] == key for row in self.datasets):
                self.datasets.append(
                    {
                        "id": key,
                        "symbol": values["symbols"][0] + values["postfix"],
                        "underlying": values["symbols"][0],
                        "timeframe": "M1" if values["kind"] == "m1" else "TICK",
                        "broker": values["broker"],
                        "bars": 0,
                    }
                )
            return {"ids": [key]}
        if route.endswith(".download.start"):
            return {"job_id": "job"}
        if route.endswith(".download.status"):
            return {
                "job_id": "job",
                "state": "succeeded",
                "outcome": "complete",
                "progress": 1.0,
            }
        if route.endswith(".download.results.read"):
            return {
                "rows": [
                    {
                        "timestamp": "2020-01-01T00:00:00+00:00",
                        "open": 1.0,
                        "high": 1.2,
                        "low": 0.9,
                        "close": 1.1,
                        "volume": 10.25,
                    }
                ],
                "dtypes": {
                    "volume": "float32",
                    "open": "float64",
                    "high": "float64",
                    "low": "float64",
                    "close": "float64",
                },
                "has_more": False,
                "next_offset": 1,
            }
        if route.endswith(".rows.read"):
            if values["dataset_id"].endswith("TICK"):
                return {
                    "rows": [
                        {
                            "DateTime": "2020-01-01T00:00:00+00:00",
                            "Ask": 1100020,
                            "Bid": 1100000,
                            "Volume": 4,
                        }
                    ],
                    "has_more": False,
                    "next_offset": 1,
                }
            return {
                "rows": [
                    {
                        "DateTime": "2020-01-01T00:00:00+00:00",
                        "Open": 1.0,
                        "High": 1.2,
                        "Low": 0.9,
                        "Close": 1.1,
                        "Volume": 10,
                    }
                ],
                "has_more": False,
                "next_offset": 1,
            }
        raise AssertionError(route)


def test_add_symbol_shared_ui_route_and_broker_postfix(tmp_path: Path) -> None:
    client = FixtureClient(tmp_path)
    assert dukascopy.add_symbol(
        symbol="GBP/USD", data_type="M1/TICK", client=client
    ) == ["GBPUSDM1", "GBPUSDTICK"]
    assert dukascopy.add_symbol(symbol="GBPUSD", client=client) == "GBPUSDM1"
    assert len(client.datasets) == 2
    requests = [
        value for route, value in client.routes if route.endswith(".definitions.add")
    ]
    assert all(
        value["broker"] == "3" and value["postfix"] == "_dukascopy"
        for value in requests
    )
    assert all(
        route.startswith("/contributions/workspace.data_manager/sources.dukascopy.")
        for route, _ in client.routes
    )


def test_cli_and_legacy_download_use_same_backend(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    client = FixtureClient(tmp_path)
    monkeypatch.setattr(dukascopy, "_client", lambda *args, **kwargs: client)
    assert (
        dukascopy._main(
            [
                "add-symbol",
                "--symbol",
                "GBPUSD",
                "--type",
                "M1",
                "--broker",
                "dukascopy",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["ids"] == "GBPUSDM1"
    output = tmp_path / "export.csv"
    assert (
        dukascopy._main(
            [
                "--symbol",
                "GBPUSD",
                "--start",
                "2020-01-01",
                "--end",
                "2020-01-01",
                "--mode",
                "overwrite",
                "--cdn",
                "CHINA",
                "--workers",
                "2",
                "--store",
                str(tmp_path),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    request = next(
        value for route, value in client.routes if route.endswith(".download.start")
    )
    assert request["overwrite"] is True
    assert request["mode"] == "cdn-cn"
    assert request["workers"] == 2
    frame = pd.read_csv(output)
    assert frame["close"].tolist() == [1.1]


@pytest.mark.parametrize("suffix", ["csv", "parquet", "feather"])
def test_atomic_output_preserves_rows(tmp_path: Path, suffix: str) -> None:
    output = tmp_path / ("export." + suffix)
    frame = pd.DataFrame({"price": [1.0, 2.0], "volume": [4, 5]})
    assert write_table_output(output, [frame.iloc[:1], frame.iloc[1:]]) == 2
    read = {"csv": pd.read_csv, "parquet": pd.read_parquet, "feather": pd.read_feather}[
        suffix
    ]
    assert read(output)["price"].tolist() == [1.0, 2.0]
    with pytest.raises(ClientError, match="No rows"):
        write_table_output(output, [])
    assert read(output)["volume"].tolist() == [4, 5]


def test_provider_definition_registration_is_idempotent(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)

    async def scenario() -> None:
        owner = "plugin.data_manager.dukascopy"
        manager = JobManager(1, 128 * 1024 * 1024)
        context = HostCapabilities(
            resources=ResourceAccess(
                owner, "1.0.0", ResourceStore(tmp_path / "resources")
            ),
            jobs=JobAccess(owner, manager),
            log=None,
            market_data=MarketAccess(owner, MarketDataStore(tmp_path, database)),
            network=NetworkAccess(owner, HistoricalNetwork()),
        )
        contribution = await dukascopy._prepare(context)
        payload: JsonValue = {
            "symbols": ["GBPUSD"],
            "kind": "m1",
            "postfix": "_research",
        }
        first = await contribution.invoke("definitions.add", payload)
        second = await contribution.invoke("definitions.add", payload)
        assert first == second
        catalog: Any = await contribution.invoke("catalog", {})
        assert len(catalog["datasets"]) == 1
        assert catalog["datasets"][0]["symbol"] == "GBPUSD_research"
        await contribution.close()
        await manager.close()

    asyncio.run(scenario())


def test_rejected_broker_and_peer_custody(tmp_path: Path) -> None:
    client = FixtureClient(tmp_path)
    with pytest.raises(ClientError, match="broker"):
        dukascopy.add_symbol(broker="unknown", client=client)
    with pytest.raises(ValueError, match="source"):
        dukascopy.add_symbol(source="yahoo", client=client)
    with pytest.raises(ClientError, match="market root"):
        dukascopy.download_data(
            "GBPUSD",
            "2020-01-01",
            "2020-01-01",
            store=tmp_path / "wrong",
            client=client,
        )


def test_disclaimer_and_no_command_need_no_host(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert dukascopy._main([]) == 0
    assert "add-symbol" in capsys.readouterr().out
    assert dukascopy._main(["--disclaimer"]) == 0
    assert "Dukascopy" in capsys.readouterr().out


def test_scan_resample_and_timezone_share_verified_rows(tmp_path: Path) -> None:
    client = FixtureClient(tmp_path)
    dukascopy.add_symbol(symbol="GBPUSD", client=client)
    frame = dukascopy._scan_market_m1(
        "GBPUSD",
        timeframe="h1",
        start="2020-01-01",
        end="2020-01-01",
        store_root=tmp_path,
        tz="Europe/London",
        client=client,
    )
    assert frame["Close"].tolist() == [1.1]
    assert str(frame["DateTime"].dt.tz) == "Europe/London"


@pytest.mark.parametrize("data_type", ["M1/TICK", "BOTH"])
def test_python_download_results_match_canonical_storage_branch(
    tmp_path: Path, data_type: str
) -> None:
    """Store-enabled source API returns integer reconstructed volumes and real prices."""
    client = FixtureClient(tmp_path)
    results = dukascopy.download_data(
        "GBPUSD",
        "2020-01-01",
        "2020-01-01",
        data_type=data_type,
        client=client,
        store=tmp_path,
    )
    candles, ticks = results["GBPUSD_M1"], results["GBPUSD_TICKS"]
    assert candles["volume"].dtype == "uint64" and candles["volume"].tolist() == [10]
    assert candles["timestamp"].dtype == "datetime64[ms, UTC]"
    assert ticks["ask"].tolist() == [1.10002] and ticks["bid"].tolist() == [1.1]
    assert ticks["ask_volume"].tolist() == ticks["bid_volume"].tolist() == [4]
    assert ticks["ask_volume"].dtype == "uint64"
    assert all(
        values["result_representation"] == "canonical"
        for route, values in client.routes
        if route.endswith("download.start")
    )


def test_python_explicit_raw_result_preserves_fractional_dtype(tmp_path: Path) -> None:
    client = FixtureClient(tmp_path)
    frame = dukascopy.download_data(
        "GBPUSD",
        "2020-01-01",
        "2020-01-01",
        client=client,
        store=tmp_path,
        result_representation="provider",
    )["GBPUSD_M1"]
    assert frame["volume"].dtype == "float32" and frame["volume"].tolist() == [10.25]
    assert frame["timestamp"].dtype == "datetime64[ms, UTC]"


def test_public_download_adapters_preserve_source_shapes(tmp_path: Path) -> None:
    client = FixtureClient(tmp_path)
    candles = dukascopy._download_candles(
        "GBPUSD",
        "h1",
        start="2020-01-01",
        end="2020-01-01",
        client=client,
        store=tmp_path,
        use_cdn=False,
    )
    ticks = dukascopy._download_ticks(
        "GBPUSD",
        "2020-01-01",
        "2020-01-01",
        client=client,
        store=tmp_path,
        use_cdn=False,
    )
    assert candles["close"].tolist() == [1.1]
    assert ticks["ask_volume"].tolist() == [4]
    assert all(
        values["mode"] == "standard"
        for route, values in client.routes
        if route.endswith("download.start")
    )
