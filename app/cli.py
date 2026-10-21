"""Headless CLI entrypoint with 7-stage host bootstrap and command dispatcher.

Description:
    Provides the headless command-line interface for HaruQuantAI (invoked via
    `uv run python -m app.cli`). Executes the progressive 7-stage host
    bootstrap state machine (CONFIGURING -> PATHS -> LOGGING -> PERSISTENCE ->
    SERVICES -> ROUTES -> READY) in headless mode (headless=True, without
    launching a Uvicorn HTTP server), dispatches operator commands (status,
    health, resources, jobs, plugins, settings, reconcile) directly against the
    live bootstrapped AppHost services, and guarantees reverse-order (LIFO)
    teardown and telemetry draining on exit.

Purpose:
    FEAT-HOST-CLI: Headless CLI entrypoint executing the 7-stage host
    bootstrap and dispatching host/workspace commands without a web server.

Key Capabilities:
    - FR-HOST-CLI-BOOTSTRAP-CONTEXT: Boot the headless AppHost through all
      7 stages (CONFIGURING -> PATHS -> LOGGING -> PERSISTENCE -> SERVICES ->
      ROUTES -> READY) via explicit AppHost lifecycle methods and guarantee
      reverse-order LIFO teardown on exit.
      Associated: `HeadlessCliRunner`, `run_cli()`
      Logging: Emits INFO on headless 7-stage startup and LIFO teardown.
    - FR-HOST-CLI-COMMAND-DISPATCH: Parse and dispatch headless CLI commands
      (status, health, resources, jobs, plugins, settings, reconcile) against
      live bootstrapped AppHost services.
      Associated: `HeadlessCliRunner.execute()`, `_build_cli_parser()`
      Logging: Emits INFO on command dispatch and WARNING/ERROR on invalid
      command arguments.
    - FR-HOST-CLI-OUTPUT-FORMATTING: Emit structured human-readable or --json
      output envelopes (ApiResponse) and return deterministic POSIX exit
      codes (0 on success, non-zero on failure).
      Associated: `format_cli_output()`, `main()`
      Logging: Emits DEBUG when serializing CLI command results.

Python API Usage:
    ```python
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
import os
from collections.abc import Callable, Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.host.bootstrap import AppHost
from app.host.logging import get_logger, shutdown_logging
from app.host.resources import get_worker_capacity, probe_hardware
from app.host.response import ApiResponse, StandardError
from app.host.settings import settings as host_settings
from app.workspace.home import HomeCLI as LandingCLI

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
    "instrument",
    "sessions",
    "home",
    "about",
    "diagnostics",
    "updates",
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
        help="Root directory for logs, scratch, and plugins.",
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
        help="Format command output as a ApiResponse JSON envelope.",
    )
    return parser


class HeadlessCliRunner:
    """Executes headless CLI commands inside an active 7-stage AppHost."""

    def __init__(self, runtime: AppHost) -> None:
        """Bind the runner to a bootstrapped ``AppHost``."""
        self.runtime = runtime

    def execute(
        self,
        command: str,
        *,
        action: str = "list",
        extra_args: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        """Dispatch ``command`` against the active ``AppHost`` services."""
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
            "instrument": lambda: self._cmd_instrument(act, extra_args),
            "sessions": lambda: self._cmd_sessions(act, extra_args),
            "home": lambda: self._cmd_home("home"),
            "about": lambda: self._cmd_home("about"),
            "diagnostics": lambda: self._cmd_home("diagnostics"),
            "updates": lambda: self._cmd_home("updates"),
        }
        handler = handlers.get(cmd)
        if handler is None:
            raise ValueError(f"Unsupported CLI command: '{command}'")
        return handler()

    def _cmd_home(self, command: str) -> dict[str, Any]:
        """Dispatch against the Home instances composed by this host."""
        home, about = self.runtime.home, self.runtime.home_about
        if home is None or about is None:
            raise RuntimeError("Home workspace is not initialized.")
        operations = {
            "home": home.index,
            "about": about.about,
            "diagnostics": about.diagnostics,
            "updates": home.check_updates,
        }
        result = operations[command]()
        return {
            "command": command,
            **result,
            "rendered": LandingCLI.format_output(result),
        }

    def _cmd_status(self) -> dict[str, Any]:
        snap = self.runtime._get_readiness()  # noqa: SLF001
        return {
            "command": "status",
            "readiness": snap.to_dict(),
            "completed_stages": [s.value for s in snap.completed_stages],
        }

    def _cmd_health(self) -> dict[str, Any]:
        res_mgr = self.runtime.resource_manager
        if res_mgr is None:
            raise RuntimeError("ResourceMonitor is not initialized.")
        report = res_mgr.inspect_resources(
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
            raise RuntimeError("ResourceMonitor is not initialized.")
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
        host_settings.reload()
        snapshot = host_settings.as_dict()
        return {
            "command": "settings",
            "action": action,
            "scopes": sorted(snapshot.keys()),
            "scope_count": len(snapshot),
        }

    def _cmd_reconcile(self) -> dict[str, Any]:
        rec_report = AppHost._reconcile_database()  # noqa: SLF001
        return {
            "command": "reconcile",
            **rec_report,
        }

    def _cmd_data(self, action: str) -> dict[str, Any]:
        """Dispatch headless data manager workspace operations."""
        dm: Any = self.runtime.data_manager
        if dm is None:
            raise RuntimeError("DataManagerWorkspace is not initialized.")

        import app.workspace.data_manager as dm_pkg
        from app.workspace.data_manager import HomeCLI

        instruments_cli: Any = getattr(dm_pkg, "InstrumentsCLI", None)
        sessions_cli: Any = getattr(dm_pkg, "SessionsCLI", None)

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
            instruments = dm.instruments.view()
            rendered = (
                instruments_cli.format_instruments_table(instruments)
                if instruments_cli is not None
                else str(instruments)
            )
            res = {
                "command": "data",
                "action": "instruments",
                "rendered": rendered,
                "count": len(instruments),
                "instruments": instruments,
            }
        elif act in ("sessions", "session"):
            sessions = dm.sessions.view()
            rendered = (
                sessions_cli.format_sessions_table(sessions)
                if sessions_cli is not None
                else str(sessions)
            )
            res = {
                "command": "data",
                "action": "sessions",
                "rendered": rendered,
                "count": len(sessions),
                "sessions": sessions,
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

    def _cmd_instrument(
        self, action: str, extra_args: Sequence[str] | None = None
    ) -> dict[str, Any]:
        """Dispatch headless instrument operations."""
        dm: Any = self.runtime.data_manager
        if dm is None:
            raise RuntimeError("DataManagerWorkspace is not initialized.")

        import app.workspace.data_manager as dm_pkg

        instruments_cli: Any = getattr(dm_pkg, "InstrumentsCLI", None)
        if instruments_cli is None:
            raise RuntimeError("InstrumentsCLI is not available.")

        all_args = list(extra_args or [])
        clean_act = action.strip()
        if clean_act:
            if "=" in clean_act:
                all_args.append(clean_act)
            else:
                all_args.insert(0, f"action={clean_act}")
        return dict(instruments_cli.dispatch(all_args, dm.instruments))

    def _cmd_sessions(
        self, action: str, extra_args: Sequence[str] | None = None
    ) -> dict[str, Any]:
        """Dispatch headless session operations."""
        dm: Any = self.runtime.data_manager
        if dm is None:
            raise RuntimeError("DataManagerWorkspace is not initialized.")

        import app.workspace.data_manager as dm_pkg

        sessions_cli: Any = getattr(dm_pkg, "SessionsCLI", None)
        if sessions_cli is None:
            raise RuntimeError("SessionsCLI is not available.")

        all_args = list(extra_args or [])
        clean_act = action.strip()
        if clean_act:
            if "=" in clean_act:
                all_args.append(clean_act)
            else:
                all_args.insert(0, f"action={clean_act}")
        return dict(sessions_cli.dispatch(all_args, dm.sessions))


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
        err_resp = ApiResponse.error(
            code=error.code,
            message=error.message,
            details=error.details,
        )
        if as_json:
            return json.dumps(err_resp, indent=2)
        return f"ERROR [{error.code}]: {error.message}"

    payload = data or {}
    if not as_json and "rendered" in payload:
        return str(payload["rendered"])

    ok_resp = ApiResponse.ok(
        data=payload,
        meta={
            "message": f"Executed CLI command '{payload.get('command', 'unknown')}'."
        },
    )
    if as_json:
        return json.dumps(ok_resp, indent=2)

    lines = [f"Command: {payload.get('command', 'unknown')}"]
    for key, val in payload.items():
        if key == "command":
            continue
        lines.append(f"  {key}: {val}")
    return "\n".join(lines)


def run_cli(argv: Sequence[str] | None = None) -> tuple[int, str]:
    """Run the 7-stage headless bootstrap, execute command, and tear down."""
    parser = _build_cli_parser()
    args, unknown = parser.parse_known_args(list(argv) if argv is not None else [])
    data_dir = Path(args.data_dir) if args.data_dir is not None else Path("data")

    host = AppHost(
        headless=True,
        debug=bool(args.debug),
        data_dir=data_dir,
        plugins_dir=args.plugins_dir,
        use_process_pool=False,
        home_release_feed_url=os.environ.get("HARUQUANTAI_RELEASE_FEED_URL"),
    )
    cmd = args.command
    logger.info(
        "%s: Starting 7-stage headless CLI bootstrap (command=%s data_dir=%s).",
        CLI_BOOTSTRAP_FR,
        cmd,
        data_dir,
        extra={"fr_id": CLI_BOOTSTRAP_FR, "command": cmd},
    )
    effective_action = args.action
    if effective_action is None:
        effective_action = args.subcommand if args.subcommand is not None else "list"

    try:
        host.startup()
        host.initialize_db()
        host.register_modules()
        host.broadcast_event(
            channel="system",
            event_type="host.ready",
            payload={
                "host_instance_id": host.host_instance_id,
                "state": host.state.value,
            },
        )
        runner = HeadlessCliRunner(host)
        result = runner.execute(cmd, action=effective_action, extra_args=unknown)
        result["stages_completed"] = len(host.completed_stages)
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
        host.shutdown()
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
    if "--data-dir" not in effective_argv:
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
