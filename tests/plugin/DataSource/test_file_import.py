"""File parsing semantics and real isolated custody publication."""

import asyncio
from pathlib import Path
from typing import Any, cast

import pytest
from app.host.capabilities import (
    HostCapabilities,
    JobAccess,
    MarketAccess,
    SettingsAccess,
)
from app.host.jobs import JobManager
from app.persistence.market import MarketDataStore, create_isolated_schema
from app.plugin.DataSource.file_import import (
    PREDEFINED_FORMATS,
    FileRequest,
    FormatSpec,
    parse_request,
    prepare,
)


def request(text: Any, format_name: Any = "MetaTrader4", **options: Any) -> Any:
    descriptor = next(fmt for fmt in PREDEFINED_FORMATS if fmt.name == format_name)
    fmt = FormatSpec(
        name=descriptor.name,
        separator=descriptor.separator,
        date_format=descriptor.date_format,
        time_format=descriptor.time_format,
        skip_rows=descriptor.skip_rows,
        skip_columns=descriptor.skip_columns,
        columns=cast("Any", tuple(descriptor.columns)),
    )
    return FileRequest(content=text, format=fmt, symbol="EURUSD", **options)


def test_source_descending_rows_and_volume_rounding() -> None:
    parsed, timeframe = parse_request(
        request(
            "2024.01.02,00:01,1.1,1.2,1.0,1.15,2.5\n"
            "2024.01.02,00:00,1.0,1.1,0.9,1.05,1.5\n"
        )
    )
    assert timeframe == "M1"
    assert parsed["volume"].tolist() == [2, 2]
    assert parsed["open"].tolist() == [1.0, 1.1]
    assert parsed["timestamp"].is_monotonic_increasing


def test_source_sparse_mt5_ticks_and_bad_line_policy() -> None:
    parsed, timeframe = parse_request(
        request(
            "date\ttime\tbid\task\n"
            "2024.01.02\t00:00:00.001\t1.0\t1.1\n"
            "2024.01.02\t00:00:00.002\t\t1.2\n",
            "MetaTrader5 Tick Data",
        )
    )
    assert timeframe == "TICK"
    assert parsed["bid"].tolist() == [1.0, 1.0]
    assert parsed["ask"].tolist() == [1.1, 1.2]
    with pytest.raises(ValueError, match="expected"):
        parse_request(request("invalid,row"))
    parsed, _ = parse_request(
        request("invalid,row\n2024.01.02,00:00,1,2,1,2,4", error_handling=1)
    )
    assert len(parsed) == 1
    assert parsed.attrs["ignored_rows"] == 1


def test_file_job_persists_real_prices_and_incoming_precedence(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)

    async def scenario() -> None:
        owner = "plugin.data_manager.file_import"
        contribution = await prepare(
            HostCapabilities(
                None,
                JobAccess(owner, JobManager(1, 512 * 1024 * 1024)),
                None,
                market_data=MarketAccess(owner, store),
            )
        )

        async def submit(content: Any) -> Any:
            started = cast(
                "Any",
                await contribution.invoke(
                    "import.start", request(content).model_dump(mode="json")
                ),
            )
            for _ in range(100):
                await asyncio.sleep(0.01)
                status = cast(
                    "Any",
                    await contribution.invoke(
                        "import.status", {"job_id": started["job_id"]}
                    ),
                )
                if status["state"] in ("failed", "succeeded"):
                    assert status["state"] == "succeeded", status
                    return status["dataset_id"]
            pytest.fail("Import did not terminate")

        dataset_id = await submit("2024.01.02,00:00,1,2,0.5,1.5,4")
        assert await submit("2024.01.02,00:00,2,3,1,2.5,6") == dataset_id
        await contribution.close()
        retained = MarketAccess("workspace.data_manager", store).read_source(dataset_id)
        assert retained.num_rows == 1
        assert retained.column("Close").to_pylist() == [2.5]
        assert retained.column("Volume").to_pylist() == [6]
        assert store.source_partitions(dataset_id)[0]["revision"] == 2

    asyncio.run(scenario())


def test_custom_formats_persist_through_host_settings_and_detection(
    tmp_path: Path,
) -> None:
    saved: dict[str, Any] = {}
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    owner = "plugin.data_manager.file_import"
    context = HostCapabilities(
        None,
        JobAccess(owner, JobManager(1, 1024)),
        None,
        settings=SettingsAccess(owner, saved),
        market_data=MarketAccess(owner, MarketDataStore(tmp_path, database)),
    )

    async def scenario() -> None:
        contribution = await prepare(context)
        fmt = request("unused").format.model_copy(update={"name": "My format"})
        cast(
            "Any",
            await contribution.invoke(
                "formats.save", {"format": fmt.model_dump(mode="json")}
            ),
        )
        with pytest.raises(ValueError, match="already exists"):
            cast(
                "Any",
                await contribution.invoke(
                    "formats.save", {"format": fmt.model_dump(mode="json")}
                ),
            )
        await contribution.close()
        restarted = await prepare(context)
        catalog = cast("Any", await restarted.invoke("catalog", {}))
        assert catalog["custom_formats"][0]["name"] == "My format"
        detected = cast(
            "Any",
            await restarted.invoke(
                "detect",
                {
                    "content": "2024.01.02,00:00,1,2,0.5,1.5,4\n2024.01.02,00:01,1,2,0.5,1.5,4"
                },
            ),
        )
        assert detected["name"] == "My format"
        cast("Any", await restarted.invoke("formats.delete", {"name": "My format"}))
        assert (cast("Any", await restarted.invoke("catalog", {})))[
            "custom_formats"
        ] == []
        await restarted.close()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("step", "expected"),
    [
        (60, "M1"),
        (300, "M5"),
        (900, "M15"),
        (1800, "M30"),
        (3600, "H1"),
        (14400, "H4"),
        (86400, "D1"),
    ],
)
def test_auto_timeframe_uses_received_spacing(step: int, expected: str) -> None:
    from datetime import UTC, datetime, timedelta

    first = datetime(2024, 1, 1, tzinfo=UTC)
    lines = [
        (first + timedelta(seconds=step * index)).strftime("%Y.%m.%d,%H:%M")
        + ",1,2,0.5,1.5,4"
        for index in range(3)
    ]
    frame, actual = parse_request(request("\n".join(lines)))
    assert actual == expected
    assert len(frame) == 3
    assert frame["close"].tolist() == [1.5, 1.5, 1.5]


def test_custom_epoch_ticks_and_preview_configuration(tmp_path: Path) -> None:
    from app.plugin.DataSource.file_import import FileRuntime

    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    owner = "plugin.data_manager.file_import"
    backing: dict[str, Any] = {}
    fmt = FormatSpec(
        name="Epoch ticks",
        separator=";",
        date_format="epoch millis",
        columns=("Date & Time", "Ask", "Bid", "Volume", "Volume"),
    )
    values = FileRequest(
        content="1704067200001;1,2;1,1;2;3\n1704067200002;1,3;1,2;4;5",
        format=fmt,
        symbol="EURUSD",
    ).model_dump(mode="json")

    async def scenario() -> None:
        jobs = JobManager(1, 512 * 1024 * 1024)
        runtime = FileRuntime(
            MarketAccess(owner, MarketDataStore(tmp_path, database)),
            JobAccess(owner, jobs),
            SettingsAccess(owner, backing),
        )
        await runtime.invoke("formats.save", {"format": fmt.model_dump(mode="json")})
        assert runtime.custom_formats()[0].name == "Epoch ticks"
        with pytest.raises(ValueError, match="exists"):
            await runtime.invoke(
                "formats.save", {"format": fmt.model_dump(mode="json")}
            )
        result = cast("Any", await runtime.invoke("preview", values))
        assert result["timeframe"] == "TICK"
        assert [row["volume"] for row in result["preview"]] == [5, 9]
        assert result["preview"][0]["ask"] == 1.2
        detected = cast(
            "Any", await runtime.invoke("detect", {"content": values["content"]})
        )
        assert detected["name"] == "Epoch ticks"
        created = cast(
            "Any",
            await runtime.invoke(
                "add", {"symbol": "EURUSD", "instrument": "EURUSD", "timeframe": "TICK"}
            ),
        )
        job = cast("Any", await runtime.invoke("import.start", values))
        await jobs.tasks[job["job_id"]]
        status = cast(
            "Any", await runtime.invoke("import.status", {"job_id": job["job_id"]})
        )
        assert status["state"] == "succeeded"
        assert status["dataset_id"] == created["id"]
        assert runtime.market.read_source_partition(created["id"], "2024-01").column(
            "Ask"
        ).to_pylist() == [1200000, 1300000]
        minute = next(
            row
            for row in runtime.market.source_definitions()
            if row["timeframe"] == "M1"
        )
        candles = runtime.market.read_source_partition(minute["id"], "2024")
        assert candles.num_rows == 1
        assert candles.column("Open").to_pylist() == [1.1]
        assert candles.column("Close").to_pylist() == [1.2]
        assert candles.column("Volume").to_pylist() == [14]
        await runtime.invoke("formats.delete", {"name": fmt.name})
        assert runtime.custom_formats() == ()
        with pytest.raises(ValueError, match="unavailable"):
            await runtime.invoke("formats.delete", {"name": fmt.name})
        with pytest.raises(ValueError, match="Unknown"):
            await runtime.invoke("unknown", {})
        await runtime.close()
        await jobs.close()

    asyncio.run(scenario())
