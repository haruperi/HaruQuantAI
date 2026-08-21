"""Main HaruQuantAI application bootstrap."""

import asyncio
import json
import os
from pathlib import Path

from app.api.control_plane import SystemControlPlane
from app.composition.config import AppConfig
from app.composition.engine import CompositionEngine

CONFIG_ENV_VAR = "HARUQUANT_CONFIG"


async def run_async(config_path: str | Path | None = None) -> dict[str, object]:
    """Boot the composition engine, reconcile desired state, and return diagnostics.

    If no configuration path is supplied, the application boots with an empty
    research profile. The process remains structurally healthy while readiness
    reports missing capabilities.
    """
    engine = CompositionEngine()
    try:
        resolved_path = Path(config_path) if config_path is not None else None
        if resolved_path is not None:
            await engine.load_and_reconcile_file(resolved_path)
        else:
            await engine.reconcile_with_config(AppConfig())

        control_plane = SystemControlPlane(engine)
        return {
            "liveness": control_plane.liveness(),
            "readiness": control_plane.readiness(),
            "capabilities": control_plane.capabilities(),
            "features": control_plane.features(),
        }
    finally:
        await engine.shutdown()


def run() -> None:
    """Run the application bootstrap and print machine-readable runtime status."""
    configured_path = os.environ.get(CONFIG_ENV_VAR)
    status = asyncio.run(run_async(configured_path))
    print(json.dumps(status, default=str, sort_keys=True))


if __name__ == "__main__":
    run()
