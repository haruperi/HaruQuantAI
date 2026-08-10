"""Yahoo channel health persistence."""

from app.services.brokers._shared.health import _record_health_checkpoint


def record_yahoo_health_checkpoint(**evidence: object) -> object:
    """Record one redacted Yahoo health checkpoint.

    Args:
        **evidence: Required checkpoint fields accepted by the shared recorder.

    Returns:
        Data-owned transaction response.

    Raises:
        TypeError: If required evidence is missing or has an invalid type.
        ValueError: If checkpoint evidence is invalid.
    """
    return _record_health_checkpoint("yahoo", **evidence)  # type: ignore[arg-type]
