"""Application composition root and CLI entry point.

This module parses command-line flags, configures structured logging,
resolves active feature sets, and manages the top-level application runtime
lifecycle with clean graceful shutdown.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from app.kernel.bootstrapper import Runtime
from app.kernel.logging import LoggingConfig, configure_logging, get_logger
from app.registry import PROFILES, available_profiles, get_features

logger = get_logger(__name__)

_LOG_LEVELS: dict[str, int] = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}


UI_DIR: Path = Path(__file__).resolve().parent / "ui"


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser.

    Returns:
        Configured `ArgumentParser` instance.
    """
    parser = argparse.ArgumentParser(
        prog="project-template",
        description="Business-neutral modular monolith starter",
    )
    profiles = ", ".join(available_profiles())
    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        help=f"Named profile to activate (available: {profiles})",
    )
    parser.add_argument(
        "--enabled",
        nargs="*",
        default=None,
        help="Explicit feature names to activate",
    )
    parser.add_argument(
        "--log-level",
        type=str.upper,
        default="INFO",
        choices=list(_LOG_LEVELS.keys()),
        help="Minimum logging severity level (default: INFO)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate dependency resolution, log sequence, and exit without running",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Output system composition diagnostics in JSON format and exit",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available configuration profiles and exit",
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Start the Vite frontend development server alongside the backend",
    )
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse runtime profile, feature selection, and diagnostic flags.

    Args:
        argv: Optional command-line argument sequence (defaults to sys.argv[1:]).

    Returns:
        Parsed `argparse.Namespace`.
    """
    return build_parser().parse_args(argv)


def _is_valid_ui_dir(ui_dir: Path) -> bool:
    """Check if the given directory contains a valid frontend package.

    Args:
        ui_dir: Path to directory to inspect.

    Returns:
        True if directory exists and contains package.json, False otherwise.
    """
    return ui_dir.is_dir() and (ui_dir / "package.json").is_file()


def _terminate_process_tree(pid: int) -> None:
    """Terminate a process and all its child processes on Windows.

    Args:
        pid: The process ID of the root process to terminate.
    """
    if sys.platform == "win32":
        taskkill_bin = shutil.which("taskkill") or r"C:\Windows\System32\taskkill.exe"
        try:
            subprocess.run(  # noqa: S603
                [taskkill_bin, "/F", "/T", "/PID", str(pid)],
                capture_output=True,
                check=False,
            )
        except OSError as exc:
            logger.warning("taskkill_failed", pid=pid, error=str(exc))


async def _run_ui_server(
    ui_dir: Path,
    stop_event: asyncio.Event | None = None,
    wait_timeout: float = 5.0,
) -> int:
    """Launch and supervise the Vite frontend development server.

    Args:
        ui_dir: Absolute path to the frontend directory containing package.json.
        stop_event: Optional asyncio Event used to signal server termination.
        wait_timeout: Maximum seconds to wait for graceful process exit before kill.

    Returns:
        Process exit code (0 on clean termination, 1 on error).
    """
    if not await asyncio.to_thread(_is_valid_ui_dir, ui_dir):
        logger.error(
            "frontend_directory_invalid",
            ui_dir=str(ui_dir),
        )
        return 1

    npm_cmd = shutil.which("npm") or shutil.which("npm.cmd") or shutil.which("npm.exe")
    if not npm_cmd:
        logger.error("npm_executable_not_found")
        return 1

    logger.info("starting_frontend_dev_server", ui_dir=str(ui_dir), cmd=npm_cmd)
    try:
        proc = await asyncio.create_subprocess_exec(
            npm_cmd,
            "run",
            "dev",
            cwd=str(ui_dir),
        )
    except OSError as exc:
        logger.error("frontend_spawn_failed", error=str(exc))
        return 1

    try:
        if stop_event is not None:
            proc_task = asyncio.create_task(proc.wait())
            stop_task = asyncio.create_task(stop_event.wait())
            _done, pending = await asyncio.wait(
                [proc_task, stop_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
        else:
            await proc.wait()
    except asyncio.CancelledError:
        logger.info("frontend_dev_server_cancelled")
        raise
    finally:
        if proc.returncode is None:
            logger.info("stopping_frontend_dev_server", pid=proc.pid)
            if sys.platform == "win32":
                _terminate_process_tree(proc.pid)
            else:
                proc.terminate()

            try:
                await asyncio.wait_for(proc.wait(), timeout=wait_timeout)
            except TimeoutError:
                proc.kill()
                await proc.wait()

    return 0


async def async_main(
    argv: Sequence[str] | None = None,
    stop_event: asyncio.Event | None = None,
) -> int:
    """Asynchronous composition root: boot features and run until shutdown.

    Args:
        argv: Optional command-line arguments to parse.
        stop_event: Optional asyncio Event used to signal server termination.

    Returns:
        Process exit code (0 on clean termination, 1 on failure).
    """
    args = parse_args(argv)

    if args.list_profiles:
        payload: dict[str, list[str]] = {
            name: sorted(features) for name, features in PROFILES.items()
        }
        print(json.dumps(payload, indent=2))
        return 0

    try:
        factories, enabled = get_features(profile=args.profile, enabled=args.enabled)
    except ValueError as err:
        print(f"Configuration error: {err}", file=sys.stderr)
        return 1

    level_num = _LOG_LEVELS.get(args.log_level, 20)
    config = LoggingConfig(level=level_num)
    exit_code = 0

    with configure_logging(config):
        logger.info(
            "application_starting",
            profile=args.profile,
            enabled=sorted(enabled) if enabled else None,
            log_level=args.log_level,
            dry_run=args.dry_run,
            ui=args.ui,
        )

        try:
            async with Runtime(factories, enabled=enabled) as runtime:
                if args.status:
                    status_info: dict[str, object] = {
                        "status": "ready",
                        "active_features": list(runtime.active_features),
                        "profile": args.profile,
                    }
                    print(json.dumps(status_info, indent=2))
                elif args.dry_run:
                    if args.ui and not await asyncio.to_thread(
                        _is_valid_ui_dir, UI_DIR
                    ):
                        logger.error(
                            "frontend_directory_invalid",
                            ui_dir=str(UI_DIR),
                        )
                        exit_code = 1
                    else:
                        if args.ui:
                            logger.info(
                                "ui_dry_run_validated",
                                ui_dir=str(UI_DIR),
                            )
                        logger.info("dry_run_completed_successfully")
                else:
                    logger.info(
                        "application_started",
                        active_features=len(runtime.active_features),
                    )
                    if args.ui:
                        exit_code = await _run_ui_server(UI_DIR, stop_event=stop_event)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("application_failed", error=str(exc))
            exit_code = 1
        finally:
            logger.info("application_stopped")

    return exit_code


def run(argv: Sequence[str] | None = None) -> None:
    """Synchronous entry point suitable for pyproject.toml console scripts.

    Args:
        argv: Optional command-line arguments.
    """
    try:
        exit_code = asyncio.run(async_main(argv))
    except KeyboardInterrupt:
        exit_code = 0
    sys.exit(exit_code)


if __name__ == "__main__":
    run()
