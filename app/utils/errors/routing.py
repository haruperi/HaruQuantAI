"""Route safe mapped error events only through caller-injected sinks."""

from collections.abc import Callable, Mapping

from app.utils.errors.mapping import map_exception

type ErrorSink = Callable[[Mapping[str, str]], None]


def route_error_event(exception: BaseException, sink: ErrorSink) -> dict[str, str]:
    """Map an exception and synchronously invoke an injected error sink.

    Args:
        exception: Exception to convert to boundary-safe evidence.
        sink: Synchronous consumer explicitly supplied by the caller.

    Returns:
        The same safe payload delivered to ``sink``.

    Raises:
        Exception: Any exception raised by the injected sink is propagated
            unchanged; Utils does not suppress or retry sink failures.
    """
    payload = map_exception(exception)
    sink(payload)
    return payload
