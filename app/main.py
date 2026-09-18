"""Application composition root and CLI entry point.

This module parses command-line flags, configures structured logging,
resolves active feature sets, and manages the top-level application runtime
lifecycle with clean graceful shutdown.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence

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
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse runtime profile, feature selection, and diagnostic flags.

    Args:
        argv: Optional command-line argument sequence (defaults to sys.argv[1:]).

    Returns:
        Parsed `argparse.Namespace`.
    """
    return build_parser().parse_args(argv)


async def async_main(argv: Sequence[str] | None = None) -> int:
    """Asynchronous composition root: boot features and run until shutdown.

    Args:
        argv: Optional command-line arguments to parse.

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

    with configure_logging(config):
        logger.info(
            "application_starting",
            profile=args.profile,
            enabled=sorted(enabled) if enabled else None,
            log_level=args.log_level,
            dry_run=args.dry_run,
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
                    return 0

                logger.info(
                    "application_started",
                    active_features=len(runtime.active_features),
                )

                if args.dry_run:
                    logger.info("dry_run_completed_successfully")
                    return 0
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("application_failed", error=str(exc))
            return 1
        finally:
            logger.info("application_stopped")

    return 0


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
