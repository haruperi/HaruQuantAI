"""Data Manager CLI uses published routes and survives absent acquisition code."""

from __future__ import annotations

import base64
import io
import json
import zipfile
from pathlib import Path
from typing import Any

import pytest
from app.cli import Client, ClientError

from scripts import data_manager_cli as cli


class RouteClient(Client):
    """Explicit host-response fixture with independently removable provider routes."""

    def __init__(self) -> None:
        super().__init__("http://127.0.0.1:8000")
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.provider_available = True
        self.response: dict[str, Any] = {
            "success": True,
            "content": "DateTime,Close\n2024-01-15,1.2\n",
        }

    def request(self, route: str, data: dict[str, Any] | None = None) -> Any:
        values = data or {}
        self.calls.append((route, values))
        if "sources." in route and not self.provider_available:
            raise ClientError("Acquisition provider unavailable")
        if route.endswith("sources.dukascopy.catalog"):
            return {
                "brokers": [{"id": "9", "name": "Dukascopy", "postfix": "_duka"}],
                "datasets": [
                    {
                        "id": "a" * 32,
                        "symbol": "GBPUSD_duka",
                        "underlying": "GBPUSD",
                        "timeframe": "M1",
                    }
                ],
            }
        if route.endswith("download.start"):
            return {"job_id": "b" * 32}
        if route.endswith("download.status"):
            return {"job_id": "b" * 32, "state": "succeeded", "outcome": "complete"}
        return self.response


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> RouteClient:
    connection = RouteClient()
    monkeypatch.setattr(cli, "_client", lambda *_args: connection)
    return connection


def test_help_needs_no_host(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main([]) == 0
    assert "HaruQuantAI Data Manager CLI" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("arguments", "operation", "kind"),
    [
        (["--data"], "actions.list_datasets", None),
        (["--instruments"], "catalogs.get", "instruments"),
        (["--sessions"], "catalogs.get", "sessions"),
        (["--stock-groups"], "catalogs.get", "groups"),
        (["--broker-profiles"], "catalogs.get", "brokers"),
        (["review", "GBPUSD"], "actions.review_data", None),
        (["review", "GBPUSD", "--quality"], "actions.review_quality", None),
        (["review", "GBPUSD", "--chart"], "actions.review_chart", None),
        (["update-all"], "actions.update_all", None),
        (["update-selected", "GBPUSD"], "actions.update_selected", None),
        (["broker-data", "--query", "GBP"], "actions.broker_data", None),
        (
            ["broker-data-update", "--profile-ids", "9"],
            "actions.broker_data_update",
            None,
        ),
        (["delete", "GBPUSD"], "actions.delete", None),
        (["clear", "GBPUSD"], "actions.delete", None),
        (["clone", "GBPUSD", "--shift-hours", "2"], "actions.clone_to_timezone", None),
    ],
)
def test_existing_commands_use_host(
    client: RouteClient,
    arguments: list[str],
    operation: str,
    kind: str | None,
) -> None:
    assert cli.main(arguments) == 0
    route, values = client.calls[-1]
    assert route == "/contributions/workspace.data_manager/" + operation
    if kind:
        assert values["kind"] == kind
    if arguments[0] == "clear":
        assert values["symbols"] == ["GBPUSD"] and values["mode"] == "clear"
    if arguments[0] == "clone":
        assert values["timezone"] == "UTC+2"
    assert not set(values).intersection(
        {"db_path", "data_root", "output_path", "file_path"}
    )


def test_absent_provider_leaves_inventory_available(client: RouteClient) -> None:
    client.provider_available = False
    assert cli.main(["--disclaimer"]) == 1
    assert cli.main(["--data"]) == 0
    assert cli.main(["--instruments"]) == 0


def test_add_resolves_real_broker(client: RouteClient) -> None:
    assert cli.main(["--add-symbol", "GBPUSD", "--broker-profile", "dukascopy"]) == 0
    assert client.calls[-1][1] == {
        "symbols": ["GBPUSD"],
        "kind": "m1",
        "broker": "9",
        "postfix": "_duka",
        "instruments": ["GBPUSD"],
    }
    assert cli.main(["--add-symbol", "GBPUSD", "--broker-profile", "absent"]) == 1


def test_download_submits_same_job(client: RouteClient) -> None:
    assert (
        cli.main(
            [
                "download",
                "GBPUSD_duka",
                "GBPUSD",
                "--start-date",
                "2024-01-15",
                "--end-date",
                "2024-01-15",
                "--overwrite",
                "--sq-cdn-cn",
            ]
        )
        == 0
    )
    request = next(
        values for route, values in client.calls if route.endswith("download.start")
    )
    assert request == {
        "dataset_id": "a" * 32,
        "date_from": "2024-01-15",
        "date_to": "2024-01-15",
        "overwrite": True,
        "mode": "cdn-cn",
    }


@pytest.mark.parametrize("command", ["export-csv", "export-mt5", "save-definitions"])
def test_export_is_client_owned(
    client: RouteClient, tmp_path: Path, command: str
) -> None:
    path = tmp_path / "export.txt"
    arguments = (
        [command, "GBPUSD", "--output-path", str(path)]
        if command != "save-definitions"
        else [command, "--file-path", str(path)]
    )
    assert cli.main(arguments) == 0
    assert path.read_text() == client.response["content"]
    client.provider_available = False
    assert cli.main(arguments) == 0


def test_load_validated_document(client: RouteClient, tmp_path: Path) -> None:
    path = tmp_path / "definitions.json"
    path.write_text(json.dumps({"datasets": [{"symbol": "GBPUSD"}], "instruments": []}))
    assert cli.main(["load-definitions", str(path)]) == 0
    assert client.calls[-1][1] == {
        "definitions": [{"symbol": "GBPUSD"}],
        "instruments": [],
    }


def test_mt4_archive_rejects_escape(client: RouteClient, tmp_path: Path) -> None:
    def archive(name: str) -> str:
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as package:
            package.writestr(name, b"hst-bytes")
        return base64.b64encode(output.getvalue()).decode()

    client.response = {"archive_base64": archive("GBPUSD.hst")}
    assert (
        cli.main(["export-mt4", "GBPUSD", "--output-dir", str(tmp_path / "export")])
        == 0
    )
    assert (tmp_path / "export/GBPUSD.hst").read_bytes() == b"hst-bytes"
    client.response = {"archive_base64": archive("../outside.hst")}
    assert (
        cli.main(["export-mt4", "GBPUSD", "--output-dir", str(tmp_path / "export")])
        == 1
    )
    assert not (tmp_path / "outside.hst").exists()


@pytest.mark.parametrize(
    "arguments",
    [
        ["--log"],
        ["--clear-log"],
        ["--data", "--db", "active.db"],
        ["--data", "--data-dir", "active"],
    ],
)
def test_unpublished_or_ambient_operations_fail_closed(
    client: RouteClient, arguments: list[str]
) -> None:
    assert cli.main(arguments) == 1
    assert not any("log" in route for route, _ in client.calls)
