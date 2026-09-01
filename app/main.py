"""Executable HaruQuantAI composition runtime."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import logging
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import uvicorn

from app.composition.config import AppConfig, load_config_from_file
from app.composition.engine import CompositionEngine
from app.composition.logging import (
    LoggingConfig,
    compute_secret_fingerprint,
    configure_logging,
    emit_cleanup_diagnostics,
)

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build the unified command-line argument parser.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="haruquantai",
        description="HaruQuantAI quantitative composition runtime and API server",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="API server bind host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API server bind port (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        dest="reload",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable/disable server auto-reload",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        help="Logging level threshold",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Optional destination file for structured log records",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to runtime configuration file",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print composition status diagnostics",
    )
    return parser


def _status_payload(engine: CompositionEngine) -> dict[str, object]:
    """Build a serialization-safe snapshot from the composition runtime.

    Args:
        engine: Active composition engine.

    Returns:
        Runtime status suitable for diagnostic JSON output.
    """
    status = engine.get_status()
    return {
        "profile": status.profile,
        "is_ready": status.is_ready,
        "missing_profile_capabilities": list(status.missing_profile_capabilities),
        "active_features": list(status.active_features),
        "active_capabilities": list(status.active_capabilities),
        "feature_states": {
            feature_id: state.value
            for feature_id, state in status.feature_states.items()
        },
        "blocked_features": status.blocked_features,
        "package_dependency_errors": status.package_dependency_errors,
        "capability_dependency_errors": status.capability_dependency_errors,
        "runtime_failures": status.runtime_failures,
        "cleanup_errors": {
            feature_id: list(errors)
            for feature_id, errors in status.cleanup_errors.items()
        },
        "replacement_reports": {
            feature_id: {
                "old_generation": report.old_generation,
                "new_generation": report.new_generation,
                "committed": report.committed,
                "rolled_back": report.rolled_back,
                "status": report.status,
                "error": report.error,
                "cleanup_errors": list(report.cleanup_errors),
                "consumer_errors": list(report.consumer_errors),
            }
            for feature_id, report in status.replacement_reports.items()
        },
        "errors": status.errors,
        "capabilities": {
            identifier: {
                "identifier": identifier,
                "is_available": True,
                "provider_feature_id": info.owner_id,
                "generation": info.generation,
                "registered_at": binding.registered_at.isoformat(),
            }
            for identifier, info in engine.registry.active_capabilities().items()
            if (binding := engine.registry.get_binding(identifier)) is not None
        },
    }


async def async_main(argv: Sequence[str] | None = None) -> int:  # noqa: C901, PLR0912, PLR0915
    """Run the composition runtime and return a process exit code.

    Returns:
        Process exit code.
    """
    parser = build_parser()
    args = parser.parse_args(args=argv if argv is not None else sys.argv[1:])

    loaded_app_config: AppConfig | None = None
    config_ref: str | None = None
    config_file_not_found = False

    if args.config is not None:
        config_path = Path(args.config)
        config_ref = compute_secret_fingerprint(str(config_path))
        if not config_path.is_file():  # noqa: ASYNC240
            config_file_not_found = True
        else:
            with contextlib.suppress(Exception):
                loaded_app_config = load_config_from_file(config_path)

    base_log_cfg = (
        loaded_app_config.logging if loaded_app_config is not None else LoggingConfig()
    )
    log_level = (
        args.log_level.upper() if args.log_level is not None else base_log_cfg.level
    )
    log_file = args.log_file if args.log_file is not None else base_log_cfg.file_path

    log_cfg = LoggingConfig(
        level=log_level,
        console=base_log_cfg.console,
        file_path=log_file,
        format="json",
        max_bytes=base_log_cfg.max_bytes,
        backup_count=base_log_cfg.backup_count,
        capture_capacity=base_log_cfg.capture_capacity,
    )
    logging_handle = configure_logging(log_cfg)

    engine: CompositionEngine | None = None
    exit_code = 0
    try:
        try:
            logger.info(
                "HaruQuantAI launcher starting",
                extra={
                    "event": "LAUNCHER_START",
                    "fields": {
                        "config_supplied": args.config is not None,
                        "config_ref": config_ref,
                        "status_mode": args.status,
                    },
                },
            )

            if config_file_not_found:
                logger.error(
                    "Configuration file not found",
                    extra={
                        "event": "CONFIG_FILE_NOT_FOUND",
                        "fields": {"config_ref": config_ref},
                    },
                )
                print(f"[ERROR] Configuration file not found: {config_ref}")
                exit_code = 1
            elif args.config is not None and loaded_app_config is None:
                logger.error(
                    "Failed to parse configuration file",
                    extra={
                        "event": "CONFIG_PARSE_FAILED",
                        "fields": {"config_ref": config_ref},
                    },
                )
                print(f"[ERROR] Failed to parse configuration file: {config_ref}")
                exit_code = 1
            else:
                engine = CompositionEngine()
                if loaded_app_config is not None:
                    report = await engine.reconcile_with_config(loaded_app_config)
                    logger.info(
                        "Configuration reconciled successfully",
                        extra={
                            "event": "CONFIG_RECONCILED",
                            "fields": {
                                "profile": engine.config.profile,
                                "started_count": len(report.started),
                                "stopped_count": len(report.stopped),
                            },
                        },
                    )

                if args.status:
                    print(json.dumps(_status_payload(engine), indent=2))
                else:
                    print(
                        f"HaruQuantAI initialized (profile='{engine.config.profile}', "
                        f"active_features={len(engine.reconciler.active_features)}). "
                        "Use --status for composition diagnostics."
                    )
        except Exception as error:
            with contextlib.suppress(Exception):
                logger.exception(
                    "Launcher execution failure",
                    extra={
                        "event": "LAUNCHER_FAILURE",
                        "fields": {"error_type": type(error).__name__},
                    },
                )
            exit_code = 1
        finally:
            if engine is not None:
                try:
                    await engine.shutdown()
                except Exception as error:
                    exit_code = 1
                    with contextlib.suppress(Exception):
                        logger.exception(
                            "Composition engine shutdown failed",
                            extra={
                                "event": "LAUNCHER_ENGINE_SHUTDOWN_FAILED",
                                "fields": {"error_type": type(error).__name__},
                            },
                        )
            try:
                logger.info(
                    "HaruQuantAI launcher shutdown complete",
                    extra={"event": "LAUNCHER_SHUTDOWN"},
                )
            except Exception:  # noqa: BLE001
                exit_code = 1
    finally:
        cleanup_diagnostics = logging_handle.close()
        if cleanup_diagnostics:
            with contextlib.suppress(Exception):
                emit_cleanup_diagnostics(cleanup_diagnostics)
            exit_code = 1
    return exit_code


def run(argv: Sequence[str] | None = None) -> None:
    """Synchronous project script entry point.

    Launches the FastAPI API server by default, or executes the composition
    diagnostics if --status is specified.

    Args:
        argv: Optional explicit command-line argument sequence.

    Raises:
        SystemExit: When --status diagnostics mode is executed.
    """
    parser = build_parser()
    args = parser.parse_args(args=argv if argv is not None else sys.argv[1:])

    if args.status:
        raise SystemExit(asyncio.run(async_main(argv)))

    log_level = args.log_level.lower() if args.log_level else "info"
    uvicorn_kwargs: dict[str, Any] = {
        "host": args.host,
        "port": args.port,
        "reload": args.reload,
        "log_level": log_level,
    }
    if not args.reload and args.workers > 1:
        uvicorn_kwargs["workers"] = args.workers

    uvicorn.run("app.services.api.composition.application:app", **uvicorn_kwargs)


if __name__ == "__main__":
    run()
