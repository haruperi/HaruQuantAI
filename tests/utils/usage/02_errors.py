"""Executable shared-error examples."""

from collections.abc import Mapping

from app.utils import (
    HaruQuantError,
    ValidationError,
    get_error_metadata,
    map_exception,
    route_error_event,
)


def example_typed_error_codes() -> HaruQuantError:
    """Create a shared typed error."""
    return ValidationError("VALIDATION_FAILED", "FIELD_MISSING")


def example_exception_payload_mapping() -> dict[str, str]:
    """Map an error without exposing raw exception text."""
    return map_exception(RuntimeError("password=unsafe"))


def example_exception_extension() -> HaruQuantError:
    """Extend the base exception in a domain."""

    class DomainError(HaruQuantError):
        """Example domain extension."""

    return DomainError("DOMAIN_FAILURE")


def example_error_metadata() -> str:
    """Normalize and look up immutable metadata."""
    return get_error_metadata("validation-failed").code


def example_route_error_event() -> list[Mapping[str, str]]:
    """Route safe evidence to an injected sink."""
    events: list[Mapping[str, str]] = []
    route_error_event(example_typed_error_codes(), events.append)
    return events


def main() -> None:
    """Run all error examples."""
    typed_error = example_typed_error_codes()
    mapped_error = example_exception_payload_mapping()
    domain_error = example_exception_extension()
    metadata_code = example_error_metadata()
    routed_events = example_route_error_event()
    assert mapped_error["code"] == "INTERNAL_ERROR"
    assert domain_error.code == "DOMAIN_FAILURE"
    assert metadata_code == "VALIDATION_FAILED"
    assert len(routed_events) == 1
    print("Typed error:", {"code": typed_error.code, "detail": typed_error.detail})
    print("Mapped exception:", mapped_error)
    print("Domain extension:", domain_error.code)
    print("Error metadata:", metadata_code)
    print("Routed error event:", dict(routed_events[0]))


if __name__ == "__main__":
    main()
