"""WF-STR-001: validate an immutable Strategy reference and configuration."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import (
    register_strategy_version,
    validate_strategy_config,
    validate_strategy_ref,
)
from tests.strategy.usage.workflows._support import (
    auth_context,
    caller_config,
    policy,
    registration_request,
    temporary_storage,
    unresolved_ref,
)

WORKFLOW_ID = "WF-STR-001"
STAGES = (
    "Accept an exact immutable create_strategy_ref and declarative create_strategy_config.",
    "Register the approved immutable version in isolated Data-backed storage.",
    "Resolve exactly one eligible create_validated_strategy_ref.",
    "Validate schema, defaults, bounds, and unknown-field policy.",
    "Return a canonical configuration hash or StandardResponse error.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Caller supplies exact identity and declarative parameters.
    _stage(1)
    ref = unresolved_ref()
    config = caller_config()
    print("Input:", ref.strategy_id, ref.exact_version, config.parameters)

    # Stage 2: Establish immutable registry truth.
    _stage(2)
    with temporary_storage():
        registration = register_strategy_version(
            registration_request(), auth_context(), policy()
        )
        if registration.data is None:
            raise RuntimeError(f"Registration failed: {registration.error}")
        print(
            "Registration:",
            registration.data.status,
            "record=",
            registration.data.record_ref,
            "audit=",
            registration.data.audit_event_ref,
            "publication_pending=",
            registration.data.publication_pending,
        )
        if registration.data.publication_pending:
            raise RuntimeError("Registration audit publication is incomplete")

        # Stage 3: Resolve the exact approved reference.
        _stage(3)
        resolved = validate_strategy_ref(ref, policy())
        print(
            "Reference:",
            resolved.status,
            resolved.data.registry_record_hash if resolved.data else resolved.error,
        )

    # Stage 4: Validate declarative configuration.
    _stage(4)
    if resolved.data is None:
        raise RuntimeError(f"Reference validation failed: {resolved.error}")
    validated = validate_strategy_config(resolved.data, config)
    print("Configuration:", validated.status)

    # Stage 5 — OUTPUT BOUNDARY: Return StandardResponse with validated hash or error.
    _stage(5)
    print(
        "Output:",
        validated.status,
        validated.data.config_hash if validated.data else validated.error,
    )


if __name__ == "__main__":
    main()
