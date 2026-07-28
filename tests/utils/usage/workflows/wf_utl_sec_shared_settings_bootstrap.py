"""WF-UTL-SEC: execute shared settings bootstrap end to end."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.utils import load_settings
from pydantic import ValidationError as PydanticValidationError

WORKFLOW_ID = "WF-UTL-SEC"
STAGES = (
    "Load explicit values and process-style overrides at the Utils boundary.",
    "Validate supported deployment and runtime settings.",
    "Return immutable settings without mutating caller input.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented settings workflow from mappings to typed settings."""
    print(f"{WORKFLOW_ID} — Shared Settings Bootstrap")
    print("INPUT BOUNDARY — explicit mapping and environment")

    # Stage 1 — Load explicit values and process-style overrides at the Utils boundary.
    _stage(1)
    explicit = {"ENVIRONMENT": "test", "LOG_RENDER": "json"}
    environment = {"RUNTIME_PROFILE": "simulation", "LOG_LEVEL": "INFO"}
    original_explicit = dict(explicit)
    original_environment = dict(environment)
    settings = load_settings(explicit, environment)
    print("Loaded precedence:", settings.environment, settings.runtime_profile)
    print("\n--- Active Application Configuration ---")
    print(f"Loaded Config Environment : {settings.environment}")
    print(f"Runtime Profile           : {settings.runtime_profile}")
    print(f"Log Level                 : {settings.logging.level}")
    print(f"Log Render Format         : {settings.logging.render}")
    print(f"Log Directory             : {settings.logging.log_directory}")

    # Stage 2 — Validate supported deployment and runtime settings.
    _stage(2)
    assert settings.environment == "test"
    assert settings.runtime_profile == "simulation"
    try:
        load_settings({"ENVIRONMENT": "unsupported"}, {})
    except Exception as exc:  # noqa: BLE001 - public loader hides internal error classes.
        print("Invalid environment rejected:", type(exc).__name__)
    else:
        raise AssertionError("invalid environment unexpectedly accepted")

    # Stage 3 — Return immutable settings without mutating caller input.
    _stage(3)
    assert explicit == original_explicit
    assert environment == original_environment
    try:
        settings.environment = "dev"  # type: ignore[misc]
    except PydanticValidationError as exc:
        print("Immutable settings verified:", type(exc).__name__)
    else:
        raise AssertionError("RuntimeSettings unexpectedly allowed mutation")

    print("OUTPUT BOUNDARY — immutable validated RuntimeSettings")


if __name__ == "__main__":
    main()
