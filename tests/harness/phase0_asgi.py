"""Run the Phase 0 real-provider ASGI browser-test boundary on loopback."""

from __future__ import annotations

import argparse
import asyncio
import sys
import tempfile
from pathlib import Path

import uvicorn
from app.services.interfaces.serve_api_events.asgi import create_api_asgi_app

from tests.services.interfaces.workspace_shared import mount_identity_stack


async def _serve(port: int) -> None:
    """Mount the real identity stack and serve it until process termination."""
    with tempfile.TemporaryDirectory(prefix="hq-phase0-asgi-") as temporary:
        database = Path(temporary) / "identity.db"
        registry, store_scope, gateway_scope = await mount_identity_stack(database)
        app = create_api_asgi_app(registry)
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=port,
            log_level="warning",
            access_log=False,
        )
        try:
            await uvicorn.Server(config).serve()
        finally:
            await gateway_scope.close()
            await store_scope.close()


def main() -> int:
    """Parse the loopback port and run the bounded ASGI harness.

    Returns:
        Process exit status after normal server termination.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("--port must be between 1024 and 65535")
    asyncio.run(_serve(args.port))
    return 0


if __name__ == "__main__":
    sys.exit(main())
