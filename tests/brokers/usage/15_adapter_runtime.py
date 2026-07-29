"""FEAT-BRK-15: exercise runtime lifecycle through a genuine provider adapter."""

import asyncio

import _support  # noqa: F401
from _support import real_session, require_success
from app.services.brokers import get_broker_connection_status, get_broker_value_field


async def _run() -> None:
    """Exercise runtime lifecycle and invocation-local result wrapping."""
    async with real_session("mt5") as adapter:
        status = await get_broker_connection_status(adapter)
        require_success("status", status)
        data = get_broker_value_field(status, "data")
        assert data is not None
        assert get_broker_value_field(data, "transport_connected")
        print("state", get_broker_value_field(data, "state"))
        metadata = get_broker_value_field(status, "metadata")
        print("latency_ms", get_broker_value_field(metadata, "execution_ms"))


def main() -> None:
    """Run the standalone genuine adapter-runtime usage program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
