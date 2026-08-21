"""Executable HaruQuantAI composition runtime."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from app.api.facade import create_api
from app.api.http import SystemHttpServer
from app.composition.engine import CompositionEngine


def _status_payload(engine: CompositionEngine) -> dict[str, object]:
    api = create_api(engine=engine)
    status = api.system.get_runtime_status()
    capabilities = api.system.list_capabilities()
    if status is None:
        return {"profile": "unknown", "is_ready": False}
    return {
        "profile": status.profile,
        "is_ready": status.is_ready,
        "missing_profile_capabilities": list(
            status.missing_profile_capabilities
        ),
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
                "identifier": info.identifier,
                "is_available": info.is_available,
                "provider_feature_id": info.provider_feature_id,
                "generation": info.generation,
                "registered_at": (
                    info.registered_at.isoformat() if info.registered_at else None
                ),
            }
            for identifier, info in capabilities.items()
        },
    }


async def async_main(argv: Sequence[str] | None = None) -> int:
    """Run the composition runtime and return a process exit code."""
    parser = argparse.ArgumentParser(
        prog="haruquantai",
        description="HaruQuantAI quantitative composition runtime",
    )
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(args=argv if argv is not None else sys.argv[1:])

    engine = CompositionEngine()
    try:
        if args.config is not None:
            config_path = Path(args.config)
            if not config_path.is_file():  # noqa: ASYNC240
                print(f"[ERROR] Configuration file not found: {config_path}")
                return 1
            await engine.load_and_reconcile_file(config_path)

        if args.status:
            print(json.dumps(_status_payload(engine), indent=2))
            return 0

        if args.serve:
            api = create_api(engine=engine)
            server = SystemHttpServer(api=api, host=args.host, port=args.port)
            print(
                "[INFO] HaruQuantAI system control plane running at "
                f"http://{args.host}:{args.port}"
            )
            try:
                await server.serve_forever()
            finally:
                await server.stop()
            return 0

        print(
            f"HaruQuantAI initialized (profile='{engine.config.profile}', "
            f"active_features={len(engine.reconciler.active_features)}). "
            "Use --status or --serve."
        )
        return 0
    finally:
        await engine.shutdown()


def run() -> None:
    """Synchronous project script entry point."""
    raise SystemExit(asyncio.run(async_main()))


if __name__ == "__main__":
    run()
