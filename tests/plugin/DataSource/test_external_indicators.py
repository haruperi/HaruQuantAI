"""Real indicator parsing, host publication and restart metadata recovery."""

import asyncio
from pathlib import Path
from typing import Any, cast

import pytest
from app.host.capabilities import JobAccess, MarketAccess, SettingsAccess
from app.host.jobs import JobManager
from app.persistence.market import MarketDataStore, create_isolated_schema
from app.plugin.DataSource.external_indicators import ImportFormat, Runtime, parse

FORMAT: dict[str, Any] = {
    "name": "Daily",
    "separator": ",",
    "skipRows": 1,
    "skipColumns": 0,
    "dateFormat": "yyyy-MM-dd",
    "columns": ["Date", "Value 1"],
}
DEFINITION: dict[str, Any] = {
    "name": "Rate",
    "type": 2,
    "values": [
        {"name": "Rate", "mt4": "", "mt5": "", "el": ""},
        {"name": "", "mt4": "", "mt5": "", "el": ""},
        {"name": "", "mt4": "", "mt5": "", "el": ""},
    ],
}


def test_strict_and_ignore_rows_duplicate_last() -> None:
    text = "Date,Value\n2024-01-01,1.25\n2024-01-01,2.5\n2024-02-30,9\n"
    with pytest.raises(ValueError, match="row 4"):
        parse(text, ImportFormat.model_validate(FORMAT), 1, False)
    records, ignored = parse(text, ImportFormat.model_validate(FORMAT), 1, True)
    assert records == [{"timestamp": 1704067200000, "values": [2.5]}]
    assert ignored == 1


def test_import_job_restart_and_clear(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)

    async def scenario() -> None:
        owner = "plugin.data_manager.indicators"
        jobs = JobManager(1, 1024**3)
        metadata: dict[str, Any] = {}
        runtime = Runtime(
            MarketAccess(owner, store),
            JobAccess(owner, jobs),
            SettingsAccess(owner, metadata),
        )
        cast(
            "Any",
            await runtime.invoke(
                "state.replace", {"definitions": [DEFINITION], "formats": []}
            ),
        )
        started = cast(
            "Any",
            await runtime.invoke(
                "import.start",
                {
                    "indicator": "Rate",
                    "text": "Date,Value\n2024-01-01,1.5\n2024-01-02,2.5\n",
                    "format": FORMAT,
                },
            ),
        )
        await asyncio.wait_for(jobs.tasks[started["job_id"]], 3)
        assert (
            cast(
                "Any",
                await runtime.invoke("import.status", {"job_id": started["job_id"]}),
            )
        )["state"] == "succeeded"
        await runtime.close()
        fresh = Runtime(
            MarketAccess(owner, store),
            JobAccess(owner, jobs),
            SettingsAccess(owner, metadata),
        )
        state = cast("Any", await fresh.invoke("state.get", {}))
        assert [row["values"] for row in state["definitions"][0]["records"]] == [
            [1.5],
            [2.5],
        ]
        assert state["definitions"][0]["timeframe"] == "D1"
        cast(
            "Any",
            await fresh.invoke(
                "state.replace",
                {
                    "revision": state["revision"],
                    "definitions": [DEFINITION],
                    "formats": [],
                },
            ),
        )
        assert (cast("Any", await fresh.invoke("state.get", {})))["definitions"][0][
            "records"
        ] == []
        await jobs.close()

    asyncio.run(scenario())
