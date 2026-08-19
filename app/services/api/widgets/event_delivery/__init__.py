"""Internal ordered event-delivery feature boundary."""

from app.services.api.widgets.event_delivery.events import (
    StreamValidationError,
    build_stream_event,
)
from app.services.api.widgets.event_delivery.orchestration import (
    StreamConnectionManager,
    StreamGapError,
    StreamLimitError,
    create_stream_connection_manager,
)

__all__ = (
    "StreamConnectionManager",
    "StreamGapError",
    "StreamLimitError",
    "StreamValidationError",
    "build_stream_event",
    "create_stream_connection_manager",
)
