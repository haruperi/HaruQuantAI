"""Missing-data planning checks actual gaps and distinguishes verified tick coverage."""

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import pytest
from app.host.persistence import HostPersistence
from app.workspace.data_manager.sources import PROVIDERS, Sources, capabilities
from app.workspace.data_manager.storage import publish_frame


@pytest.fixture
def environment(tmp_path):
    database = tmp_path / "coverage.db"
    sqlite3.connect(database).close()
    calls = []

    class Provider:
        value = 1.2

        def get_bars(self, symbol, timeframe, *, date_from, date_to, **kwargs):
            calls.append((date_from, date_to))
            from app.include.enums import Timeframe

            dates = pd.date_range(
                date_from,
                date_to,
                freq=pd.Timedelta(seconds=Timeframe.resolve(timeframe).to_seconds()),
            )
            return pd.DataFrame(
                {
                    **{
                        column: [self.value] * len(dates)
                        for column in ["Open", "High", "Low", "Close"]
                    },
                    "Volume": 7,
                },
                index=dates,
            )

        def get_ticks(self, symbol, *, date_from, date_to, **kwargs):
            calls.append((date_from, date_to))
            return pd.DataFrame(
                {"Bid": [1.1], "Ask": [1.10001], "Flags": [3]},
                index=pd.to_datetime([date_from], utc=True),
            )

        def disconnect(self):
            pass

    service = Sources(
        HostPersistence(database),
        market_root=tmp_path / "market",
        client_factory=lambda _: Provider(),
    )
    return service, calls


def _legacy(service, *, timeframe="M1", dates=None, source="coinbase"):
    row = service.add(source, [{"symbol": "TEST", "timeframe": timeframe}])["data"][
        "records"
    ][0]
    frame = pd.DataFrame(
        {
            **dict.fromkeys(["Open", "High", "Low", "Close"], [1.1] * len(dates)),
            "Volume": 1,
        },
        index=pd.to_datetime(dates, utc=True),
    )
    publish_frame(service.gateway, service.market_root / source, row, frame, 1e-8)
    return service.record(row["id"])


@pytest.mark.parametrize("source", PROVIDERS)
def test_completed_download_skips_network_for_every_source(environment, source):
    service, calls = environment
    factory = service.client_factory
    timeframe = capabilities(source)["default_timeframe"]
    row = service.add(source, [{"symbol": "TEST", "timeframe": timeframe}])["data"][
        "records"
    ][0]
    service.download(row["id"], "2025-01-06", "2025-01-06")
    old = service.record(row["id"])
    path = json.loads(old["lineage_json"])["partitions"][0]
    before = Path(path).read_bytes()
    calls.clear()
    service.client_factory = lambda _: pytest.fail(
        "Cached download opened the provider"
    )
    result = service.download(row["id"], "2025-01-06", "2025-01-06")
    assert result["data"]["already_downloaded"]
    assert result["data"]["received_rows"] == 0
    assert not calls
    assert Path(path).read_bytes() == before
    assert service.record(row["id"])["updated_at"] == old["updated_at"]
    provider = factory(source)
    provider.value = 1.3
    service.client_factory = lambda _: provider
    replaced = service.download(row["id"], "2025-01-06", "2025-01-06", overwrite=True)
    assert calls and replaced["data"]["received_rows"] > 0
    assert all(
        value == 130000000 for value in pq.ParquetFile(path).read()["Open"].to_pylist()
    )


def test_internal_bar_gap_is_fetched_without_refetching_existing_bars(environment):
    service, calls = environment
    row = _legacy(service, dates=["2025-01-06T00:00:00Z", "2025-01-06T00:02:00Z"])
    result = service.download(
        row["id"], "2025-01-06T00:00:00Z", "2025-01-06T00:02:59.999999Z"
    )
    assert calls == [
        (
            datetime(2025, 1, 6, 0, 1, tzinfo=UTC),
            datetime(2025, 1, 6, 0, 1, 59, 999999, tzinfo=UTC),
        )
    ]
    assert result["data"]["record"]["bars"] == 3
    path = json.loads(result["data"]["record"]["lineage_json"])["partitions"][0]
    assert pq.ParquetFile(path).read()["Open"].to_pylist() == [
        110000000,
        120000000,
        110000000,
    ]


def test_overwrite_fetches_again_and_replaces_only_the_selected_range(environment):
    service, calls = environment
    row = _legacy(
        service,
        dates=["2025-01-06T00:00:00Z", "2025-01-06T00:01:00Z", "2025-01-06T00:02:00Z"],
    )
    result = service.download(
        row["id"], "2025-01-06T00:01:00Z", "2025-01-06T00:01:59Z", overwrite=True
    )
    assert len(calls) == 1
    path = json.loads(result["data"]["record"]["lineage_json"])["partitions"][0]
    assert pq.ParquetFile(path).read()["Open"].to_pylist() == [
        110000000,
        120000000,
        110000000,
    ]


def test_missing_daily_bar_is_not_hidden_by_catalog_minimum_and_maximum(environment):
    service, calls = environment
    row = _legacy(
        service,
        source="yahoo",
        timeframe="D1",
        dates=["2025-01-06T14:30:00Z", "2025-01-08T14:30:00Z"],
    )
    result = service.download(row["id"], "2025-01-06", "2025-01-08")
    assert calls == [
        (
            datetime(2025, 1, 7, tzinfo=UTC),
            datetime(2025, 1, 7, 23, 59, 59, 999999, tzinfo=UTC),
        )
    ]
    assert result["data"]["record"]["bars"] == 3


def test_legacy_ticks_do_not_claim_continuous_coverage_from_min_max(environment):
    service, calls = environment
    row = service.add("darwinex", [{"symbol": "TEST", "timeframe": "TICK"}])["data"][
        "records"
    ][0]
    frame = pd.DataFrame(
        {"Bid": [1.1, 1.1], "Ask": [1.10001, 1.10001], "Flags": [3, 3]},
        index=pd.to_datetime(
            ["2025-01-06T00:00:00Z", "2025-01-06T00:02:00Z"], utc=True
        ),
    )
    publish_frame(service.gateway, service.market_root / "darwinex", row, frame, 1e-8)
    service.download(row["id"], "2025-01-06", "2025-01-06")
    assert len(calls) == 1
    calls.clear()
    result = service.download(row["id"], "2025-01-06", "2025-01-06")
    assert result["data"]["already_downloaded"] and not calls


def test_missing_physical_file_is_downloaded_again(environment):
    service, calls = environment
    row = service.add("coinbase", [{"symbol": "TEST"}])["data"]["records"][0]
    result = service.download(row["id"], "2025-01-06", "2025-01-06")
    path = Path(json.loads(result["data"]["record"]["lineage_json"])["partitions"][0])
    path.unlink()
    calls.clear()
    result = service.download(row["id"], "2025-01-06", "2025-01-06")
    assert calls and path.is_file() and result["data"]["received_rows"] > 0


def test_clear_invalidates_completed_coverage(environment):
    from app.workspace.data_manager.data import Data

    service, calls = environment
    row = service.add("coinbase", [{"symbol": "TEST"}])["data"]["records"][0]
    service.download(row["id"], "2025-01-06", "2025-01-06")
    assert Data(service.gateway).clear(row["id"])["success"]
    assert json.loads(service.record(row["id"])["lineage_json"])["covered_ranges"] == []
    calls.clear()
    service.download(row["id"], "2025-01-06", "2025-01-06")
    assert calls


def test_confirmed_closed_gap_is_not_queried_again(environment, monkeypatch):
    service, calls = environment
    row = _legacy(service, dates=["2025-01-06T00:00:00Z", "2025-01-06T00:02:00Z"])
    provider = service.client_factory("coinbase")

    def empty(*args, **kwargs):
        calls.append(True)
        return pd.DataFrame()

    monkeypatch.setattr(provider, "get_bars", empty)
    service.client_factory = lambda _: provider
    result = service.download(row["id"], "2025-01-06T00:00:00Z", "2025-01-06T00:02:59Z")
    assert result["success"] and result["data"]["received_rows"] == 0 and calls
    calls.clear()
    result = service.download(row["id"], "2025-01-06T00:00:00Z", "2025-01-06T00:02:59Z")
    assert result["data"]["already_downloaded"] and not calls


def test_cached_mt5_cli_does_not_start_or_require_a_terminal_listener(
    environment, monkeypatch
):
    import argparse

    from app.workspace.brokers import metatrader
    from app.workspace.data_manager import sources_cli

    service, calls = environment
    row = service.add("mt5", [{"symbol": "TEST", "timeframe": "M1"}])["data"][
        "records"
    ][0]
    service.download(row["id"], "2025-01-06", "2025-01-06")
    monkeypatch.setattr(sources_cli, "Sources", lambda: service)
    monkeypatch.setattr(
        metatrader,
        "create_mt5_client",
        lambda: pytest.fail("Cached CLI opened MT5 listener"),
    )
    calls.clear()
    result = sources_cli.run_source_command(
        argparse.Namespace(
            resource="mt5",
            source_command="download",
            symbol="TEST",
            timeframe="M1",
            date_from="2025-01-06",
            date_to="2025-01-06",
            overwrite=False,
        ),
        None,
    )
    assert result["success"] and result["data"]["already_downloaded"] and not calls


def test_partial_feed_tail_is_not_marked_as_already_downloaded(
    environment, monkeypatch
):
    service, calls = environment
    provider = service.client_factory("coinbase")
    original = provider.get_bars

    def limited(*args, **kwargs):
        frame = original(*args, **kwargs)
        return frame.iloc[:2] if len(calls) == 1 else frame

    monkeypatch.setattr(provider, "get_bars", limited)
    service.client_factory = lambda _: provider
    row = service.add("coinbase", [{"symbol": "TEST"}])["data"]["records"][0]
    first = service.download(row["id"], "2025-01-06T00:00:00Z", "2025-01-06T00:04:59Z")
    assert first["data"]["record"]["bars"] == 2
    second = service.download(row["id"], "2025-01-06T00:00:00Z", "2025-01-06T00:04:59Z")
    assert calls[-1][0] == datetime(2025, 1, 6, 0, 2, tzinfo=UTC)
    assert second["data"]["received_rows"] == 3
    assert second["data"]["record"]["bars"] == 5
