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
import shlex
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
    "symbol",
    "brokerprofile",
    "home",
    "about",
    "diagnostics",
    "updates",
)

_SHORT_ALIASES: dict[str, list[str]] = {
    "-l": ["symbol", "action=list"],
    "-a": ["symbol", "action=add"],
    "-e": ["symbol", "action=edit"],
    "-d": ["symbol", "action=delete"],
    "-c": ["symbol", "action=clear"],
    "-il": ["instrument", "action=list"],
    "-ia": ["instrument", "action=add"],
    "-ie": ["instrument", "action=edit"],
    "-id": ["instrument", "action=delete"],
    "-ir": ["instrument", "action=refresh"],
    "-u": ["data", "action=update"],
    "-di": ["data", "action=import"],
    "-tz": ["data", "action=timezones"],
}

_FLAG_COMMANDS: dict[str, str] = {
    "-symbol": "symbol",
    "-instrument": "instrument",
    "-data": "data",
    "-brokerprofile": "brokerprofile",
    "-sessions": "sessions",
}


def _normalize_cli_args(argv: Sequence[str]) -> list[str]:
    raw_tokens: list[str] = []
    i = 0
    token_list = list(argv)
    while i < len(token_list):
        arg_item = token_list[i]
        if arg_item.startswith("--args="):
            _, val = arg_item.split("=", 1)
            raw_tokens.extend(shlex.split(val))
        elif arg_item == "--args" and i + 1 < len(token_list):
            i += 1
            raw_tokens.extend(shlex.split(token_list[i]))
        else:
            raw_tokens.append(arg_item)
        i += 1

    normalized: list[str] = []
    for arg_item in raw_tokens:
        if arg_item in _SHORT_ALIASES:
            normalized.extend(_SHORT_ALIASES[arg_item])
        elif arg_item in _FLAG_COMMANDS:
            normalized.append(_FLAG_COMMANDS[arg_item])
        else:
            normalized.append(arg_item)
    return normalized


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
            "data": lambda: self._cmd_data(act, extra_args),
            "instrument": lambda: self._cmd_instrument(act, extra_args),
            "sessions": lambda: self._cmd_sessions(act, extra_args),
            "symbol": lambda: self._cmd_symbol(act, extra_args),
            "brokerprofile": lambda: self._cmd_brokerprofile(act, extra_args),
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

    def _dispatch_legacy_data(self, dm: Any, act: str, action: str) -> dict[str, Any]:
        """Dispatch legacy sub-actions for data workspace command."""
        import app.workspace.data_manager as dm_pkg
        from app.workspace.data_manager import HomeCLI

        instruments_cli: Any = getattr(dm_pkg, "InstrumentsCLI", None)
        sessions_cli: Any = getattr(dm_pkg, "SessionsCLI", None)

        def _handle_logs() -> dict[str, Any]:
            entries = (
                dm.log.data_log(limit=50)
                if hasattr(dm.log, "data_log")
                else dm.log.list_logs(limit=50)
            )
            return {
                "command": "data",
                "action": "logs",
                "count": len(entries),
                "logs": [e if isinstance(e, dict) else e.to_dict() for e in entries],
            }

        dispatch_map: dict[str, Callable[[], dict[str, Any]]] = {
            "home": lambda: {
                "command": "data",
                "action": "home",
                "rendered": HomeCLI.format_home_dashboard(
                    dm.home.get_overview(), dm.home.get_saved_datasets()
                ),
                "overview": dm.home.get_overview(),
                "saved_datasets": [ds.to_dict() for ds in dm.home.get_saved_datasets()],
            },
            "datasets": lambda: {
                "command": "data",
                "action": "datasets",
                "count": len(dm.data.list_datasets()),
                "datasets": [d.to_dict() for d in dm.data.list_datasets()],
            },
            "instruments": lambda: {
                "command": "data",
                "action": "instruments",
                "rendered": (
                    instruments_cli.format_instruments_table(
                        dm.instruments.instruments()
                    )
                    if instruments_cli is not None
                    else str(dm.instruments.instruments())
                ),
                "count": len(dm.instruments.instruments()),
                "instruments": dm.instruments.instruments(),
            },
            "sessions": lambda: {
                "command": "data",
                "action": "sessions",
                "rendered": (
                    sessions_cli.format_sessions_table(dm.sessions.view())
                    if sessions_cli is not None
                    else str(dm.sessions.view())
                ),
                "count": len(dm.sessions.view()),
                "sessions": dm.sessions.view(),
            },
            "baskets": lambda: {
                "command": "data",
                "action": "baskets",
                "count": len(dm.baskets.baskets()),
                "baskets": dm.baskets.baskets(),
            },
            "brokers": lambda: {
                "command": "data",
                "action": "brokers",
                "count": len(dm.broker.brokers()),
                "brokers": dm.broker.brokers(),
            },
            "providers": lambda: {
                "command": "data",
                "action": "providers",
                "count": len(dm.connections.list_providers()),
                "providers": [p.to_dict() for p in dm.connections.list_providers()],
            },
            "logs": _handle_logs,
        }
        alias_map = {
            "overview": "home",
            "dashboard": "home",
            "list": "home",
            "status": "home",
            "dataset": "datasets",
            "instrument": "instruments",
            "session": "sessions",
            "basket": "baskets",
            "stock_groups": "baskets",
            "broker": "brokers",
            "provider": "providers",
            "log": "logs",
        }
        target = alias_map.get(act, act)
        handler = dispatch_map.get(target)
        if handler is None:
            raise ValueError(f"Unsupported data action: '{action}'")
        return handler()

    def _cmd_data(
        self, action: str, extra_args: Sequence[str] | None = None
    ) -> dict[str, Any]:
        """Dispatch headless data manager workspace operations."""
        dm: Any = self.runtime.data_manager
        if dm is None:
            raise RuntimeError("AppDataManager is not initialized.")

        import app.workspace.data_manager as dm_pkg

        all_args = list(extra_args or [])
        clean_act = action.strip()
        if clean_act:
            if "=" in clean_act:
                all_args.append(clean_act)
            else:
                all_args.insert(0, f"action={clean_act}")

        params = dict(a.split("=", 1) for a in all_args if "=" in a)
        data_act = params.get("action", clean_act).lower()
        if data_act in ("update", "import", "timezones") or (
            data_act == "list"
            and any(
                k in params
                for k in ("symbols", "symbol", "datasource", "source", "csv")
            )
        ):
            data_cli: Any = getattr(dm_pkg, "DataCLI", None)
            if data_cli is not None:
                return dict(data_cli.dispatch_data(all_args, dm.data))

        act = action.strip().lower()
        return self._dispatch_legacy_data(dm, act, action)

    def _cmd_instrument(
        self, action: str, extra_args: Sequence[str] | None = None
    ) -> dict[str, Any]:
        """Dispatch headless instrument operations."""
        dm: Any = self.runtime.data_manager
        if dm is None:
            raise RuntimeError("AppDataManager is not initialized.")

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
        trading_factory = getattr(dm, "trading_factory", None)
        try:
            return dict(
                instruments_cli.dispatch(
                    all_args, dm.instruments, trading_factory=trading_factory
                )
            )
        except TypeError:
            return dict(instruments_cli.dispatch(all_args, dm.instruments))

    def _cmd_sessions(
        self, action: str, extra_args: Sequence[str] | None = None
    ) -> dict[str, Any]:
        """Dispatch headless session operations."""
        dm: Any = self.runtime.data_manager
        if dm is None:
            raise RuntimeError("AppDataManager is not initialized.")

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

    def _cmd_symbol(
        self, action: str, extra_args: Sequence[str] | None = None
    ) -> dict[str, Any]:
        """Dispatch headless symbol operations."""
        dm: Any = self.runtime.data_manager
        if dm is None:
            raise RuntimeError("AppDataManager is not initialized.")

        import app.workspace.data_manager as dm_pkg

        data_cli: Any = getattr(dm_pkg, "DataCLI", None)
        if data_cli is None:
            raise RuntimeError("DataCLI is not available.")

        all_args = list(extra_args or [])
        clean_act = action.strip()
        if clean_act:
            if "=" in clean_act:
                all_args.append(clean_act)
            else:
                all_args.insert(0, f"action={clean_act}")
        return dict(data_cli.dispatch_symbol(all_args, dm.data))

    def _cmd_brokerprofile(
        self, action: str, extra_args: Sequence[str] | None = None
    ) -> dict[str, Any]:
        """Dispatch headless broker profile operations."""
        dm: Any = self.runtime.data_manager
        if dm is None:
            raise RuntimeError("AppDataManager is not initialized.")

        import app.workspace.data_manager as dm_pkg

        broker_cli: Any = getattr(dm_pkg, "BrokerCLI", None)
        if broker_cli is None:
            raise RuntimeError("BrokerCLI is not available.")

        all_args = list(extra_args or [])
        clean_act = action.strip()
        if clean_act:
            if "=" in clean_act:
                all_args.append(clean_act)
            else:
                all_args.insert(0, f"action={clean_act}")
        return dict(broker_cli.dispatch(all_args, dm.broker))


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
    normalized_argv = _normalize_cli_args(list(argv) if argv is not None else [])
    parser = _build_cli_parser()
    args, unknown = parser.parse_known_args(normalized_argv)
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
