"""Main application entry point and executable composition runtime."""

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from app.api.facade import create_api
from app.api.http import SystemHttpServer
from app.composition.engine import CompositionEngine


async def async_main(argv: Sequence[str] | None = None) -> int:
    """Run asynchronous application composition runtime.

    Args:
        argv: Command-line arguments sequence (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 for success, non-zero for fatal configuration/runtime error).
    """
    parser = argparse.ArgumentParser(
        prog="haruquantai",
        description="HaruQuantAI Quantitative Financial Trading System",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to application TOML configuration file.",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print machine-readable runtime status diagnostics as JSON and exit.",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start the system control plane HTTP server.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host interface to bind control plane server to (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind control plane server to (default: 8000).",
    )

    args = parser.parse_args(args=argv if argv is not None else sys.argv[1:])

    engine = CompositionEngine()
    try:
        if args.config is not None:
            config_file = Path(args.config)
            if not config_file.exists():  # noqa: ASYNC240
                print(f"[ERROR] Configuration file not found: {config_file}")
                return 1
            await engine.load_and_reconcile_file(config_file)

        api = create_api(engine=engine)

        if args.status:
            status = api.system.get_runtime_status()
            caps = api.system.list_capabilities()
            status_dict = {
                "profile": status.profile if status else "default",
                "is_ready": status.is_ready if status else False,
                "missing_profile_capabilities": (
                    list(status.missing_profile_capabilities) if status else []
                ),
                "active_features": (list(status.active_features) if status else []),
                "active_capabilities": (
                    list(status.active_capabilities) if status else []
                ),
                "feature_states": (
                    {k: v.value for k, v in status.feature_states.items()}
                    if status
                    else {}
                ),
                "blocked_features": (status.blocked_features if status else {}),
                "package_dependency_errors": (
                    status.package_dependency_errors if status else {}
                ),
                "capability_dependency_errors": (
                    status.capability_dependency_errors if status else {}
                ),
                "errors": status.errors if status else {},
                "capabilities": {
                    k: {
                        "identifier": v.identifier,
                        "is_available": v.is_available,
                        "provider_feature_id": v.provider_feature_id,
                        "generation": v.generation,
                        "registered_at": (
                            v.registered_at.isoformat() if v.registered_at else None
                        ),
                    }
                    for k, v in caps.items()
                },
            }
            print(json.dumps(status_dict, indent=2))
            return 0

        if args.serve:
            server = SystemHttpServer(api=api, host=args.host, port=args.port)
            print(
                f"[INFO] HaruQuantAI system control plane running at http://{args.host}:{args.port}"
            )
            await server.serve_forever()
            return 0

        profile_name = engine.config.profile
        print(
            f"HaruQuantAI initialized (Profile: '{profile_name}'). "
            f"Active features: {len(engine.reconciler.active_features)}. "
            f"Use --status or --serve."
        )
        return 0
    finally:
        await engine.shutdown()


def run() -> None:
    """Synchronous entry point for project.scripts."""
    exit_code = asyncio.run(async_main())
    sys.exit(exit_code)


if __name__ == "__main__":
    run()
