"""Standalone ordered API stream usage."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.api import create_stream_manager, normalize_stream_event


async def _run() -> None:
    """Publish, resume, consume, and clean one stream connection."""
    manager = create_stream_manager(
        max_connections_per_actor=1,
        max_connections_process=4,
        resume_window=8,
        queue_size=4,
    )
    event = normalize_stream_event(
        {"sequence": 1, "event_type": "payload", "state": "ready"},
        {
            "request_id": "req-stream-usage-0001",
            "trace_id": "trace-stream-usage-0001",
            "route": "/api/v1/events",
        },
    )
    await manager.publish(event)
    await manager.open(
        connection_id="usage-connection",
        actor_id="usage-actor",
        resume_after=0,
    )
    stream = manager.events("usage-connection")
    received = await anext(stream)
    await stream.aclose()
    assert manager.connection_count == 0
    print({"sequence": received.sequence, "event_type": received.event_type})


def main() -> None:
    """Run ordered stream usage evidence."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
