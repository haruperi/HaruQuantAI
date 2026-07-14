"""Run real typed-error, metadata, mapping, and routing examples."""

import sys
from collections.abc import Mapping
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import (
    HaruQuantError,
    ValidationError,
    get_error_metadata,
    map_exception,
    normalize_error_code,
    route_error_event,
)


def example_typed_error_codes() -> None:
    """Illustrate raising and catching a typed symbolic error code."""
    print("\n1. Raising typed error codes")
    try:
        raise ValidationError("VALIDATION_FAILED", "FIELD_MISSING")
    except HaruQuantError as error:
        print("Caught:", error.code, error.detail)


def example_error_metadata() -> None:
    """Illustrate normalizing and looking up immutable error metadata."""
    print("\n2. Normalizing and looking up error metadata")
    code = normalize_error_code("validation-failed")
    metadata = get_error_metadata(code)
    print("Metadata:", metadata.code, metadata.title, metadata.severity)


def example_exception_extension() -> None:
    """Illustrate a domain-owned extension of the shared base error."""
    print("\n3. Extending the shared base error")

    class StrategyError(HaruQuantError):
        """Example domain-owned typed error."""

    error = StrategyError("STRATEGY_INVALID")
    print("Domain error:", error.code)


def example_exception_payload_mapping() -> None:
    """Illustrate mapping an exception to secret-safe boundary evidence."""
    print("\n4. Exception payload mapping helpers")
    payload = map_exception(ValidationError("VALIDATION_FAILED", "FIELD_MISSING"))
    print("Mapped payload:", payload)


def example_route_error_event() -> None:
    """Illustrate routing a mapped event to an injected real sink."""
    print("\n5. Routing error events")
    events: list[Mapping[str, str]] = []
    payload = route_error_event(
        ValidationError("VALIDATION_FAILED", "FIELD_MISSING"),
        events.append,
    )
    assert events == [payload]
    print("Routed event:", events[0])


if __name__ == "__main__":
    example_typed_error_codes()
    example_error_metadata()
    example_exception_extension()
    example_exception_payload_mapping()
    example_route_error_event()
