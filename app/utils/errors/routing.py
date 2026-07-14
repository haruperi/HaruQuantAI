"""Explicit routing of safe mapped error events."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from app.utils.errors.mapping import map_exception

type ErrorSink = Callable[[Mapping[str, str]], None]


def route_error_event(
    exception: BaseException,
    sink: ErrorSink,
) -> dict[str, str]:
    """Map an exception and synchronously invoke an injected error sink.

    Args:
        exception: Exception to map to boundary-safe evidence.
        sink: Explicit destination callable. Sink failures propagate unchanged.

    Returns:
        The same safe payload delivered to the sink.
    """
    payload = map_exception(exception)
    sink(payload)
    return payload
