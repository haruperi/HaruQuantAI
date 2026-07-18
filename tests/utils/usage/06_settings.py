"""Executable runtime settings examples."""

import sys
from pathlib import Path

# Add project root to path before importing local modules
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils.settings import load_settings, resolve_secret_reference


def _header(title: str) -> None:
    """Print the header for an example section.

    Args:
        title: The title of the section to display.
    """
    print(f"\n\n\n{'=' * 100}")
    print(f"\t\t{title}\t")
    print(f"{'=' * 100}\n")


_header("Example 1: Loads runtime settings from environment files, or defaults.")
settings = load_settings()
print("Environment:", settings.environment)
print("Log Level:", settings.logging.level)

_header("Example 2: Loads runtime settings from overrides.")
settings = load_settings(
    explicit_values={
        "ENVIRONMENT": "production",
        "LOG_LEVEL": "INFO",
    }
)
print("Environment:", settings.environment)
print("Log Level:", settings.logging.level)

_header("Example 3: Resolves a secret value from a reference.")
resolved = resolve_secret_reference(
    "secret://db/password", lambda _ref: "my_database_password_123"
)
print("Resolved secret value (masked):", resolved)
print("Resolved secret value (unmasked):", resolved.get_secret_value())
