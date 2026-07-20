"""Executable shared-error examples."""

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


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def example_typed_error_codes() -> None:
    """Display boundary-safe symbolic exception evidence."""
    _header("Example 1: Typed Error Codes")
    error = ValidationError("VALIDATION_FAILED", "FIELD_MISSING")
    print("Typed error:", error.code, error.detail)


def example_exception_payload_mapping() -> None:
    """Map an unexpected exception without exposing its text."""
    _header("Example 2: Exception Payload Mapping")
    print("Mapped error:", map_exception(ValueError("unsafe source detail")))


def example_exception_extension() -> None:
    """Demonstrate a domain-owned shared-base extension."""
    _header("Example 3: Exception Extension")

    class DomainError(HaruQuantError):
        """Example domain error."""

    print("Extended error:", DomainError("DOMAIN_FAILURE").code)


def example_error_metadata() -> None:
    """Normalize and retrieve immutable safe metadata."""
    _header("Example 4: Error Metadata")
    code = normalize_error_code("validation-failed")
    print("Error metadata:", get_error_metadata(code).title)


def example_route_error_event() -> None:
    """Route one safe payload through an injected sink."""
    _header("Example 5: Route Error Event")
    events: list[Mapping[str, str]] = []
    route_error_event(ValidationError("VALIDATION_FAILED"), events.append)
    print("Routed error event:", events[0]["code"])


def main() -> None:
    """Run all shared-error examples."""
    example_typed_error_codes()
    example_exception_payload_mapping()
    example_exception_extension()
    example_error_metadata()
    example_route_error_event()


if __name__ == "__main__":
    main()
