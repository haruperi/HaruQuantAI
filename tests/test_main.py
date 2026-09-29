"""Host entrypoint, maintenance, and real client/server lifecycle checks.

Configuration and browser tests use injected values or doubles. Subprocess smoke
tests select temporary data roots and loopback ports, exercise the actual CLI,
and request authenticated graceful shutdown. No test migrates the shared store;
subprocess environment filtering prevents HARU_ overrides from selecting it.
"""

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
from app.cli import Client
from app.host.bootstrap import STAGES
from app.host.settings import HostSettings
from app.main import arguments, bind_socket


def test_arguments_do_not_override_unspecified_settings():
    """Keep omitted CLI fields absent so lower-precedence configuration survives."""
    assert arguments([]) == {}
    assert arguments(["--port", "8012"])["port"] == 8012


def test_port_fallback_retains_reserved_socket(tmp_path):
    """Reserve a fallback port while the requested loopback port remains occupied."""
    with socket.socket() as occupied:
        occupied.bind(("127.0.0.1", 0))
        port = occupied.getsockname()[1]
        settings = HostSettings(port=port, data_dir=tmp_path)
        bound = bind_socket(settings)
        try:
            assert bound.getsockname()[1] > port
        finally:
            bound.close()


def test_real_host_cli_handshake_and_shutdown(tmp_path):
    """Verify complete boot logs and real CLI readiness against an isolated host.

    Asserts all five phases before client attachment and independent client readiness,
    then requests authenticated shutdown and checks exit status. A finally block
    terminates only the test-owned subprocess if the normal lifecycle fails.
    """
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("HARU_")
    }
    root = Path(__file__).resolve().parents[1]
    installation = tmp_path / "installation"
    installation.mkdir(parents=True, exist_ok=True)
    env["HARU_INSTALLATION_ROOT"] = str(installation)
    with (tmp_path / "host-output.txt").open("w+") as output:
        process = subprocess.Popen(
            [
                sys.executable,
                "app/main.py",
                "--port",
                str(port),
                "--data-dir",
                str(tmp_path / "data"),
            ],
            cwd=root,
            env=env,
            stdout=output,
            stderr=output,
        )
        try:
            client = Client(f"http://127.0.0.1:{port}")
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    output.seek(0)
                    pytest.fail(output.read())
                try:
                    if client.request("/status")["status"] == "SERVER_READY":
                        break
                except OSError:
                    pass
                time.sleep(0.05)
            else:
                pytest.fail("Host readiness deadline")
            boot_log = (tmp_path / "host-output.txt").read_text()
            for stage, label in STAGES:
                assert f"{stage} {label}: succeeded" in boot_log
            assert "Host ready: state=SERVER_READY" in boot_log
            assert "Boot scan totals: presets=0; catalog descriptors=0" in boot_log
            assert "Client initialized" not in boot_log
            assert "no_registered_provider" not in boot_log
            snapshot = client.request("/status")["boot"]
            assert snapshot["schema_version"] == 2
            assert all(s["outcome"] == "succeeded" for s in snapshot["stages"])
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "app.cli",
                    "--url",
                    client.url,
                    "--page=login",
                    "--json",
                ],
                cwd=root,
                env=env,
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            assert result.returncode == 0, result.stderr
            assert json.loads(result.stdout)["ready"]
            client.token = client.request("/auth/login", {"username": "operator"})[
                "token"
            ]
            assert client.request("/shutdown", {})["shutdown"] == "requested"
            assert process.wait(timeout=15) == 0
            boot_log = (tmp_path / "host-output.txt").read_text()
            assert "Client initialized after" in boot_log
            assert boot_log.count("Host ready: state=SERVER_READY") == 1
            assert "Boot summary" not in boot_log
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)


def test_main_reports_configuration_failure_without_creating_data(
    tmp_path, monkeypatch
):
    """Reject an invalid configured port before creating the temporary database."""
    from app.main import main

    monkeypatch.setenv("HARU_DATA_DIR", str(tmp_path))
    assert main(["--port", "0"]) == 1
    assert not (tmp_path / "database").exists()


def test_optional_browser_launch_failure_is_nonfatal(monkeypatch):
    """Convert browser rejection or webbrowser.Error into a nonfatal False result."""
    import webbrowser

    from app.main import launch

    monkeypatch.setattr(webbrowser, "open", lambda url: False)
    assert not launch("http://127.0.0.1:8000")

    def fail(url: str) -> bool:
        """Simulate the browser API failing without launching an external
        application."""
        raise webbrowser.Error("unavailable")

    monkeypatch.setattr(webbrowser, "open", fail)
    assert not launch("http://127.0.0.1:8000")


def test_maintenance_command_migrates_without_starting_server(tmp_path):
    """Run maintenance twice against a temporary legacy database.

    Verify both subprocesses exit successfully, schema verification passes, and
    server socket reservation is never logged. The second run exercises idempotence.
    """
    from app.persistence.host import ensure_schema, prepare_boot_database

    path = tmp_path / "database" / "haruquantai.db"
    ensure_schema(path)
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("HARU_")
    }
    for _ in range(2):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "app.main",
                "--data-dir",
                str(tmp_path),
                "--migrate-auth-schema",
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "Auth migration:" in result.stderr
        assert "Port reserved" not in result.stderr
        prepare_boot_database(path)


def test_listening_summary_precedes_optional_browser_launch(tmp_path, monkeypatch):
    import asyncio

    import uvicorn
    from app.host.bootstrap import BootstrapCoordinator
    from app.main import HostServer

    settings = HostSettings(data_dir=tmp_path, open_browser=True)
    host = BootstrapCoordinator(settings, installation_root=tmp_path / "installation")
    order = []

    async def fake_startup(
        server: uvicorn.Server, sockets: list[socket.socket] | None = None
    ) -> None:
        server.started = True

    monkeypatch.setattr(uvicorn.Server, "startup", fake_startup)
    monkeypatch.setattr(host, "log_boot_summary", lambda: order.append("ready"))
    monkeypatch.setattr("app.main.launch", lambda url: order.append("browser"))
    server = HostServer(uvicorn.Config("unused:app"), host)

    async def run() -> None:
        await host.initialize()
        try:
            with socket.socket() as bound:
                bound.bind(("127.0.0.1", 0))
                await server.startup([bound])
            assert order == ["ready", "browser"]
            assert host.startup.snapshot().state == "SERVER_READY"
        finally:
            await host.close()

    asyncio.run(run())
