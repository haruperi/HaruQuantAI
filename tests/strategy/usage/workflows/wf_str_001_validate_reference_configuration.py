"""WF-STR-001: validate an immutable Strategy reference and configuration."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import (
    StrategyConfig,
    StrategyEnvironment,
    StrategyRef,
    register_strategy_version,
    validate_strategy_config,
    validate_strategy_ref,
)
from tests.strategy.unit.test_catalog import make_registration
from tests.strategy.unit.test_models import COR, REQ, make_auth, make_policy
from tests.strategy.usage.workflows._support import temporary_storage

WORKFLOW_ID = "WF-STR-001"
STAGES = (
    "Accept an exact immutable StrategyRef and declarative StrategyConfig.",
    "Register the approved immutable version in isolated Data-backed storage.",
    "Resolve exactly one eligible ValidatedStrategyRef.",
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
    ref = StrategyRef(
        strategy_id="mean-reversion",
        exact_version="1.0.0",
        environment=StrategyEnvironment.RESEARCH,
        request_id=REQ,
        correlation_id=COR,
    )
    config = StrategyConfig(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        config_schema_version="v1",
        parameters={"period": 5},
        request_id=REQ,
    )
    print("Input:", ref.strategy_id, ref.exact_version, config.parameters)

    # Stage 2: Establish immutable registry truth.
    _stage(2)
    with temporary_storage():
        registration = register_strategy_version(
            make_registration(), make_auth(), make_policy()
        )
        print("Registration:", registration.status)

        # Stage 3: Resolve the exact approved reference.
        _stage(3)
        resolved = validate_strategy_ref(ref, make_policy())
        print("Reference:", resolved.status)

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
