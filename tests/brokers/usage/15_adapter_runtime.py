"""FEAT-BRK-15: exercise runtime lifecycle through a genuine provider adapter."""

import asyncio

import _support  # noqa: F401
from _support import real_session, require_success
from app.services.brokers import BrokerId


async def _run() -> None:
    """Exercise runtime lifecycle and invocation-local result wrapping."""
    async with real_session(BrokerId.MT5) as adapter:
        status = await adapter.get_connection_status()
        require_success("status", status)
        assert status.data is not None
        assert status.data.transport_connected
        print("state", status.data.state.value)
        print("latency_ms", status.latency_ms)


def main() -> None:
    """Run the standalone genuine adapter-runtime usage program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
