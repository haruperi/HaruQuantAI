"""Executable runtime-settings examples."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import (
    ConfigurationError,
    LoggingSettings,
    RuntimeSettings,
    load_settings,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def fr_utils_022_construct_configuration() -> None:
    """FR-UTL-022: Construct immutable generic settings directly."""
    _header("Example 1: Construct Configuration")
    settings = RuntimeSettings(logging=LoggingSettings(log_directory=None))
    print("Constructed settings:", settings.environment, settings.runtime_profile)


def fr_utils_023_load_active_configuration() -> None:
    """FR-UTL-023: Load explicit values over a supplied environment mapping."""
    _header("Example 2: Load Active Configuration")
    settings = load_settings(
        {"ENVIRONMENT": "test"},
        {"RUNTIME_PROFILE": "simulation"},
    )
    print("Active settings:", settings.environment, settings.runtime_profile)


def fr_utils_024_environment_constraints() -> None:
    """FR-UTL-024: Demonstrate exact environment-value validation."""
    _header("Example 3: Environment Constraints")
    try:
        load_settings({"ENVIRONMENT": "invalid"}, {})
    except ConfigurationError:
        print("Environment constraint: invalid value rejected")


def fr_utils_024_validate_settings() -> None:
    """FR-UTL-024: Demonstrate unknown-key rejection without mutation."""
    _header("Example 4: Validate Settings")
    source = {"UNKNOWN": "value"}
    try:
        load_settings(source, {})
    except ConfigurationError:
        print("Settings validation: unknown key rejected", source)


def main() -> None:
    """Run all runtime-settings examples."""
    fr_utils_022_construct_configuration()
    fr_utils_023_load_active_configuration()
    fr_utils_024_environment_constraints()
    fr_utils_024_validate_settings()


if __name__ == "__main__":
    main()
