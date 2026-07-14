"""Demonstrate runtime configuration and settings loading using Pydantic."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import (
    ConfigurationError,
    LoggingSettings,
    RuntimeSettings,
    load_settings,
    resolve_secret_reference,
)


def example_load_active_configuration() -> None:
    """Illustrate loading active application configuration."""
    print("\n1. Loading active application configuration")
    settings = load_settings(
        {"RUNTIME_PROFILE": "simulation", "LOG_LEVEL": "DEBUG"},
        {"ENVIRONMENT": "test", "LOG_RENDER": "human"},
    )
    print(
        "Active:",
        settings.environment,
        settings.runtime_profile,
        settings.logging.level,
    )


def example_environment_constraints() -> None:
    """Illustrate fail-closed environment constraints."""
    print("\n2. Environment constraints")
    try:
        load_settings({"ENVIRONMENT": "local"}, {})
    except ConfigurationError as error:
        print("Rejected unsupported environment:", error.code)
    else:
        raise AssertionError("unsupported environment was accepted")


def example_validate_settings() -> None:
    """Illustrate direct settings validation."""
    print("\n3. Validating settings")
    try:
        LoggingSettings(level="VERBOSE")  # type: ignore[arg-type]
    except ConfigurationError as error:
        print("Rejected invalid log level:", error.code)
    else:
        raise AssertionError("invalid log level was accepted")


def example_construct_configuration() -> None:
    """Illustrate constructing immutable runtime configuration."""
    print("\n4. Constructing configuration")
    settings = RuntimeSettings(
        environment="dev",
        runtime_profile="research",
        logging=LoggingSettings(level="INFO", render="json"),
    )
    print("Constructed:", settings.model_dump(mode="json"))


def example_resolve_secret_reference() -> None:
    """Illustrate explicit injected secret-reference resolution."""
    secret = resolve_secret_reference(
        "secret://broker/demo",
        lambda _reference: "resolved-secret",
    )
    print("Resolved secret remains masked:", str(secret))


if __name__ == "__main__":
    example_load_active_configuration()
    example_environment_constraints()
    example_validate_settings()
    example_construct_configuration()
    example_resolve_secret_reference()
