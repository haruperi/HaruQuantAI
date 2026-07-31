"""Executable runtime-settings examples."""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import load_broker_provider_settings, load_settings


def _feature_header(title: str) -> None:
    """Print feature title and module flow banner."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'-' * 88}\n{title}\n{'-' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def fr_utils_023_load_active_configuration() -> None:
    """FR-UTL-023: Stage 1 & 3 — Load explicit values + environment with precedence order."""
    _header(
        "Stage 1 & 3: Active Configuration Loading - Explicit Values + Environment -> Immutable RuntimeSettings (FR-UTL-023)"
    )
    settings = load_settings(
        {"ENVIRONMENT": "test"},
        {"RUNTIME_PROFILE": "simulation"},
    )
    print(_format_result(settings))
    print(
        f"Data -> environment='{settings.environment}', runtime_profile='{settings.runtime_profile}'"
    )


def fr_utils_023_load_broker_provider_configuration() -> None:
    """FR-UTL-023: Stage 1 & 3 — Load secret-redacting broker settings through opaque API."""
    _header(
        "Stage 1 & 3: Broker Provider Configuration - Explicit Values + Environment -> Opaque Broker Settings (FR-UTL-023)"
    )
    settings = load_broker_provider_settings()
    provider_data = {
        "mt5": settings.mt5_enabled,
        "ctrader": settings.ctrader_enabled,
        "binance": settings.binance_enabled,
        "dukascopy": settings.dukascopy_enabled,
        "yahoo": settings.yahoo_enabled,
    }
    print(_format_result(settings))
    print(f"Data -> provider_enablement: {provider_data}")


def fr_utils_024_environment_constraints() -> None:
    """FR-UTL-024: Stage 2 — Demonstrate strict validation rejecting invalid environment values."""
    _header(
        "Stage 2: Strict Validation - Environment Constraints Rejection (FR-UTL-024)"
    )
    try:
        load_settings({"ENVIRONMENT": "invalid"}, {})
    except Exception as exc:  # noqa: BLE001 - public loader intentionally hides error classes.
        print(_format_result(exc))
        print(f"Data -> Environment constraint: invalid value rejected ({exc})")


def fr_utils_024_validate_settings() -> None:
    """FR-UTL-024: Stage 2 — Demonstrate strict validation rejecting unknown configuration keys without mutation."""
    _header("Stage 2: Strict Validation - Unknown Key Rejection (FR-UTL-024)")
    source = {"UNKNOWN": "value"}
    try:
        load_settings(source, {})
    except Exception as exc:  # noqa: BLE001 - public loader intentionally hides error classes.
        print(_format_result(exc))
        print(
            f"Data -> Settings validation: unknown key rejected from {source} ({exc})"
        )


def fr_utils_022_construct_configuration() -> None:
    """FR-UTL-022: Stage 3 — Construct immutable generic settings directly."""
    _header(
        "Stage 3: Immutable RuntimeSettings construction - Construct Configuration (FR-UTL-022)"
    )
    settings = load_settings({"ENVIRONMENT": "test"}, {})
    print(_format_result(settings))
    print(
        f"Data -> environment='{settings.environment}', runtime_profile='{settings.runtime_profile}'"
    )


def main() -> None:
    """Run all runtime-settings examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-UTIL-06 — settings/ — Runtime Settings\n\n"
        "Purpose: Define immutable generic runtime/logging settings and provide the sole\n"
        "repository app/configs/env.json loading base for typed domain settings.\n\n"
        "Module flow:\n"
        "-> explicit values + environment\n"
        "-> strict validation\n"
        "-> immutable RuntimeSettings"
    )

    # Stage 1 & 3: Input mapping and configuration loading
    fr_utils_023_load_active_configuration()
    fr_utils_023_load_broker_provider_configuration()

    # Stage 2: Strict validation and fail-closed checks
    fr_utils_024_environment_constraints()
    fr_utils_024_validate_settings()

    # Stage 3: Immutable settings output construction
    fr_utils_022_construct_configuration()


if __name__ == "__main__":
    main()
