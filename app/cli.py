"""Headless CLI entrypoint with 7-stage host bootstrap and command dispatcher.

Description:
    Provides the headless command-line interface for HaruQuantAI (invoked via
    `uv run python -m app.cli`, mirroring SQX's `sqcli` / `SQConsoleStarter`).
    Executes the progressive 7-stage host bootstrap state machine
    (CONFIGURING -> PATHS -> LOGGING -> PERSISTENCE -> SERVICES -> ROUTES ->
    READY) in headless mode (headless=True, without launching a Uvicorn HTTP
    server), dispatches operator commands (status, health, resources, jobs,
    plugins, settings, reconcile) directly against the live bootstrapped
    HostRuntime services, and guarantees reverse-order (LIFO) teardown and
    telemetry draining on exit.

Purpose:
    FEAT-HOST-CLI: Headless CLI entrypoint executing the 7-stage host
    bootstrap and dispatching host/workspace commands without a web server.

Key Capabilities:
    - FR-HOST-CLI-BOOTSTRAP-CONTEXT: Boot the headless HostRuntime through all
      7 stages (CONFIGURING -> PATHS -> LOGGING -> PERSISTENCE -> SERVICES ->
      ROUTES -> READY) via bootstrap_context(headless=True) and guarantee
      reverse-order LIFO teardown on exit.
      Associated: `HeadlessCliRunner`, `run_cli()`
      Logging: Emits INFO on headless 7-stage startup and LIFO teardown.
    - FR-HOST-CLI-COMMAND-DISPATCH: Parse and dispatch headless CLI commands
      (status, health, resources, jobs, plugins, settings, reconcile) against
      live bootstrapped HostRuntime services.
      Associated: `HeadlessCliRunner.execute()`, `_build_cli_parser()`
      Logging: Emits INFO on command dispatch and WARNING/ERROR on invalid
      command arguments.
    - FR-HOST-CLI-OUTPUT-FORMATTING: Emit structured human-readable or --json
      output envelopes (StandardResponse) and return deterministic POSIX exit
      codes (0 on success, non-zero on failure).
      Associated: `format_cli_output()`, `main()`
      Logging: Emits DEBUG when serializing CLI command results.

Python API Usage:
    ```python
    from pathlib import Path
    from app.cli import run_cli

    exit_code, output = run_cli(["status", "--json", "--data-dir", "data"])
    assert exit_code == 0
    ```

CLI Usage:
    ```bash
    uv run python -m app.cli status --json
    uv run python -m app.cli health
    uv run python -m app.cli resources
    uv run python -m app.cli jobs --action list
    uv run python -m app.cli plugins --action list
    ```
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.host.bootstrap import (
    BootstrapConfig,
    HostRuntime,
    bootstrap_context,
    reconcile_database,
)
from app.host.logging import get_logger, shutdown_logging
from app.host.resources import get_worker_capacity, probe_hardware
from app.host.response import StandardError, StandardResponse
from app.host.settings import settings as host_settings

__all__ = [
    "HeadlessCliRunner",
    "format_cli_output",
    "run_cli",
]

logger = get_logger(__name__)

CLI_BOOTSTRAP_FR = "FR-HOST-CLI-BOOTSTRAP-CONTEXT"
CLI_DISPATCH_FR = "FR-HOST-CLI-COMMAND-DISPATCH"
CLI_OUTPUT_FR = "FR-HOST-CLI-OUTPUT-FORMATTING"

SUPPORTED_CLI_COMMANDS: tuple[str, ...] = (
    "status",
    "health",
    "resources",
    "jobs",
    "plugins",
    "settings",
    "reconcile",
    "data",
)


def _build_cli_parser() -> argparse.ArgumentParser:
    """Construct the argument parser for the headless CLI."""
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description="HaruQuantAI Headless CLI (7-Stage Bootstrap)",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="status",
        choices=SUPPORTED_CLI_COMMANDS,
        help="Headless command to execute after 7-stage bootstrap.",
    )
    parser.add_argument(
        "subcommand",
        nargs="?",
        default=None,
        help="Subcommand or action for command (e.g. 'home' for 'data home').",
    )
    parser.add_argument(
        "--action",
        type=str,
        default=None,
        help="Sub-action for jobs/plugins/settings/data commands (default: list).",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Root directory for database, logs, scratch, and plugins.",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Explicit SQLite database file path override.",
    )
    parser.add_argument(
        "--plugins-dir",
        type=Path,
        default=None,
        help="Explicit dynamic plugins directory override.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable debug logging during CLI execution.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Format command output as a StandardResponse JSON envelope.",
    )
    return parser


class HeadlessCliRunner:
    """Executes headless CLI commands inside an active 7-stage HostRuntime."""

    def __init__(self, runtime: HostRuntime) -> None:
        """Bind the runner to a bootstrapped ``HostRuntime``."""
        self.runtime = runtime

    def execute(self, command: str, *, action: str = "list") -> dict[str, Any]:
        """Dispatch ``command`` against the active ``HostRuntime`` services."""
        cmd = command.strip().lower()
        act = action.strip().lower()
        logger.info(
            "%s: Dispatching headless CLI command '%s' (action='%s').",
            CLI_DISPATCH_FR,
            cmd,
            act,
            extra={
                "fr_id": CLI_DISPATCH_FR,
                "command": cmd,
                "action": act,
            },
        )
        handlers: dict[str, Callable[[], dict[str, Any]]] = {
            "status": self._cmd_status,
            "health": self._cmd_health,
            "resources": self._cmd_resources,
            "jobs": lambda: self._cmd_jobs(act),
            "plugins": lambda: self._cmd_plugins(act),
            "settings": lambda: self._cmd_settings(act),
            "reconcile": self._cmd_reconcile,
            "data": lambda: self._cmd_data(act),
        }
        handler = handlers.get(cmd)
        if handler is None:
            raise ValueError(f"Unsupported CLI command: '{command}'")
        return handler()

    def _cmd_status(self) -> dict[str, Any]:
        snap = self.runtime.get_readiness()
        return {
            "command": "status",
            "readiness": snap.to_dict(),
            "completed_stages": [s.value for s in snap.completed_stages],
        }

    def _cmd_health(self) -> dict[str, Any]:
        res_mgr = self.runtime.resource_manager
        if res_mgr is None:
            raise RuntimeError("ResourceManager is not initialized.")
        report = res_mgr.get_system_health(
            db_path=self.runtime.config.resolved_db_path,
            root_path=self.runtime.config.data_dir,
        )
        return {
            "command": "health",
            "status": report.status,
            "database": asdict(report.database),
            "storage": asdict(report.storage),
        }

    def _cmd_resources(self) -> dict[str, Any]:
        res_mgr = self.runtime.resource_manager
        if res_mgr is None:
            raise RuntimeError("ResourceManager is not initialized.")
        hw = probe_hardware()
        cap = get_worker_capacity()
        wd = res_mgr.check_memory_headroom()
        return {
            "command": "resources",
            "cpu_logical_cores": hw.cpu_count_logical,
            "ram_available_pct": round(100.0 - hw.ram_used_pct, 2),
            "allocated_workers": cap.allocated_workers,
            "worker_mode": cap.mode,
            "watchdog_pressured": wd.is_pressured,
            "watchdog_action": wd.recommended_action,
        }

    def _cmd_jobs(self, action: str) -> dict[str, Any]:
        job_mgr = self.runtime.job_manager
        if job_mgr is None:
            raise RuntimeError("JobManager is not initialized.")
        if action == "reconcile":
            reconciled = job_mgr.reconcile_orphan_jobs()
            return {
                "command": "jobs",
                "action": "reconcile",
                "reconciled_orphan_jobs": reconciled,
            }
        jobs = job_mgr.list_jobs(limit=50)
        return {
            "command": "jobs",
            "action": "list",
            "max_workers": job_mgr.max_workers,
            "count": len(jobs),
            "jobs": [j.to_dict() for j in jobs],
        }

    def _cmd_plugins(self, action: str) -> dict[str, Any]:
        plugin_mgr = self.runtime.plugin_manager
        if plugin_mgr is None:
            raise RuntimeError("PluginLifecycleManager is not initialized.")
        if action == "slots":
            slots = plugin_mgr.discovery.slot_registry.list_slots()
            return {
                "command": "plugins",
                "action": "slots",
                "count": len(slots),
                "slots": [s.model_dump() for s in slots],
            }
        report = plugin_mgr.build_report()
        return {
            "command": "plugins",
            "action": "list",
            "total_discovered": report.total_discovered,
            "enabled_count": report.enabled_count,
            "quarantined_count": report.quarantined_count,
            "load_order": list(report.load_order),
        }

    def _cmd_settings(self, action: str) -> dict[str, Any]:
        host_settings.reload(conn=self.runtime.config.resolved_db_path)
        snapshot = host_settings.as_dict()
        return {
            "command": "settings",
            "action": action,
            "scopes": sorted(snapshot.keys()),
            "scope_count": len(snapshot),
        }

    def _cmd_reconcile(self) -> dict[str, Any]:
        rec_report = reconcile_database(self.runtime.config.resolved_db_path)
        return {
            "command": "reconcile",
            **rec_report,
        }

    def _cmd_data(self, action: str) -> dict[str, Any]:
        """Dispatch headless data manager workspace operations."""
        dm = self.runtime.data_manager
        if dm is None:
            raise RuntimeError("DataManagerWorkspace is not initialized.")

        from app.workspace.data_manager import HomeCLI, InstrumentsCLI

        act = action.strip().lower()
        res: dict[str, Any]
        if act in ("home", "overview", "dashboard", "list", "status"):
            overview = dm.home.get_overview()
            saved_datasets = dm.home.get_saved_datasets()
            rendered = HomeCLI.format_home_dashboard(overview, saved_datasets)
            res = {
                "command": "data",
                "action": "home",
                "rendered": rendered,
                "overview": overview,
                "saved_datasets": [ds.to_dict() for ds in saved_datasets],
            }
        elif act in ("datasets", "dataset"):
            datasets = dm.data.list_datasets()
            res = {
                "command": "data",
                "action": "datasets",
                "count": len(datasets),
                "datasets": [d.to_dict() for d in datasets],
            }
        elif act in ("instruments", "instrument"):
            instruments = dm.instruments.list_instruments()
            rendered = InstrumentsCLI.format_instruments_table(instruments)
            res = {
                "command": "data",
                "action": "instruments",
                "rendered": rendered,
                "count": len(instruments),
                "instruments": [i.to_dict() for i in instruments],
            }
        elif act in ("sessions", "session"):
            sessions = dm.sessions.list_sessions()
            res = {
                "command": "data",
                "action": "sessions",
                "count": len(sessions),
                "sessions": [s.to_dict() for s in sessions],
            }
        elif act in ("baskets", "basket", "stock_groups"):
            overview_items = dm.baskets.get_baskets_overview()
            res = {
                "command": "data",
                "action": "baskets",
                "count": len(overview_items),
                "baskets": [b.to_dict() for b in overview_items],
            }
        elif act in ("brokers", "broker"):
            brokers = dm.broker.list_brokers()
            res = {
                "command": "data",
                "action": "brokers",
                "count": len(brokers),
                "brokers": [b.to_dict() for b in brokers],
            }
        elif act in ("providers", "provider"):
            providers = dm.connections.list_providers()
            res = {
                "command": "data",
                "action": "providers",
                "count": len(providers),
                "providers": [p.to_dict() for p in providers],
            }
        elif act in ("logs", "log"):
            logs = dm.log.list_logs(limit=50)
            res = {
                "command": "data",
                "action": "logs",
                "count": len(logs),
                "logs": [entry.to_dict() for entry in logs],
            }
        else:
            raise ValueError(f"Unsupported data action: '{action}'")
        return res


def format_cli_output(
    data: dict[str, Any] | None,
    *,
    as_json: bool = False,
    error: StandardError | None = None,
) -> str:
    """Format CLI execution output as human-readable text or JSON envelope."""
    logger.debug(
        "%s: Formatting CLI output (as_json=%s is_error=%s).",
        CLI_OUTPUT_FR,
        as_json,
        error is not None,
        extra={"fr_id": CLI_OUTPUT_FR},
    )
    if error is not None:
        err_resp = StandardResponse.failure(
            message=error.message,
            error=error,
        )
        if as_json:
            return json.dumps(err_resp.to_dict(), indent=2)
        return f"ERROR [{error.code}]: {error.message}"

    payload = data or {}
    if not as_json and "rendered" in payload:
        return str(payload["rendered"])

    ok_resp = StandardResponse.success(
        data=payload,
        message=f"Executed CLI command '{payload.get('command', 'unknown')}'.",
    )
    if as_json:
        return json.dumps(ok_resp.to_dict(), indent=2)

    lines = [f"Command: {payload.get('command', 'unknown')}"]
    for key, val in payload.items():
        if key == "command":
            continue
        lines.append(f"  {key}: {val}")
    return "\n".join(lines)


def run_cli(argv: Sequence[str] | None = None) -> tuple[int, str]:
    """Run the 7-stage headless bootstrap, execute command, and tear down."""
    parser = _build_cli_parser()
    args = parser.parse_args(list(argv) if argv is not None else [])
    data_dir = Path(args.data_dir) if args.data_dir is not None else Path("data")

    config = BootstrapConfig(
        headless=True,
        debug=bool(args.debug),
        data_dir=data_dir,
        db_path=args.db_path,
        plugins_dir=args.plugins_dir,
        use_process_pool=False,
    )
    logger.info(
        "%s: Starting 7-stage headless CLI bootstrap (command=%s data_dir=%s).",
        CLI_BOOTSTRAP_FR,
        args.command,
        data_dir,
        extra={"fr_id": CLI_BOOTSTRAP_FR, "command": args.command},
    )
    effective_action = args.action
    if effective_action is None:
        effective_action = args.subcommand if args.subcommand is not None else "list"

    try:
        with bootstrap_context(config) as runtime:
            runner = HeadlessCliRunner(runtime)
            result = runner.execute(args.command, action=effective_action)
            result["stages_completed"] = len(runtime.completed_stages)
        output = format_cli_output(result, as_json=bool(args.json))
        return 0, output
    except Exception as exc:
        logger.exception(
            "%s: Headless CLI command '%s' failed.",
            CLI_DISPATCH_FR,
            args.command,
            extra={"fr_id": CLI_DISPATCH_FR},
        )
        err = StandardError(
            code="CLI_EXECUTION_ERROR",
            message=str(exc) or "Command execution failed.",
        )
        return 1, format_cli_output(None, as_json=bool(args.json), error=err)
    finally:
        logger.info(
            "%s: Headless CLI teardown complete; draining telemetry.",
            CLI_BOOTSTRAP_FR,
            extra={"fr_id": CLI_BOOTSTRAP_FR},
        )
        shutdown_logging()


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for `uv run python -m app.cli`."""
    import sys
    import tempfile

    effective_argv = list(argv) if argv is not None else sys.argv[1:]
    if "--data-dir" not in effective_argv and "--db-path" not in effective_argv:
        if Path("data").is_dir():
            code, rendered = run_cli(effective_argv)
            print(rendered)
            return code
        with tempfile.TemporaryDirectory(
            prefix="hqai_cli_run_",
            ignore_cleanup_errors=True,
        ) as tmp_dir:
            code, rendered = run_cli([*effective_argv, "--data-dir", tmp_dir])
            print(rendered)
            return code

    code, rendered = run_cli(effective_argv)
    print(rendered)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
