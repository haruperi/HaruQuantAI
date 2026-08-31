"""Command-line entry point for the HaruQuantAI application server.

Provides the canonical CLI runner invoked by `haruquantai` console script.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

import uvicorn

from app.services.api.widgets.settings.bootstrap import get_api_settings


def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line argument parser for the application runner.

    Returns:
        Configured ArgumentParser instance.
    """
    settings = get_api_settings()
    parser = argparse.ArgumentParser(
        prog="haruquantai",
        description="HaruQuantAI Quantitative Financial Trading System API Server",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=settings.api_host,
        help=f"Bind socket host address (default: {settings.api_host})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.api_port,
        help=f"Bind socket port (default: {settings.api_port})",
    )
    parser.add_argument(
        "--reload",
        dest="reload",
        action="store_true",
        default=(settings.environment == "dev"),
        help="Enable auto-reload on source file changes (default in dev environment)",
    )
    parser.add_argument(
        "--no-reload",
        dest="reload",
        action="store_false",
        help="Disable auto-reload",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help=(
            "Number of worker processes (default: 1; only used when reload is disabled)"
        ),
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Logging level for the server (default: info)",
    )
    return parser


def run(args: Sequence[str] | None = None) -> None:
    """Run the HaruQuantAI FastAPI application server via Uvicorn.

    Args:
        args: Optional command-line argument list. Defaults to `sys.argv[1:]`.
    """
    parser = build_parser()
    parsed_args = parser.parse_args(args=args if args is not None else sys.argv[1:])

    app_target = "app.services.api.composition.application:app"

    if parsed_args.reload:
        uvicorn.run(
            app_target,
            host=parsed_args.host,
            port=parsed_args.port,
            reload=True,
            log_level=parsed_args.log_level,
        )
    else:
        uvicorn.run(
            app_target,
            host=parsed_args.host,
            port=parsed_args.port,
            reload=False,
            workers=parsed_args.workers,
            log_level=parsed_args.log_level,
        )


if __name__ == "__main__":
    run()
