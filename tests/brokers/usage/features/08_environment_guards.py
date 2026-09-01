"""FEAT-BRK-08: simulation and live isolation evidence."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import register_broker_environment_permission

import _support  # noqa: F401


def fr_brokers_139_150_environment_guard() -> None:
    """Demonstrate deterministic denial of direct live mutation permission.

    Returns:
        None.
    """
    try:
        register_broker_environment_permission(
            "mt5",
            "redacted-demo-account",
            "live",
            allow_read=True,
            allow_mutation=True,
            effective_from="2026-08-10T00:00:00+00:00",
            request_id="req-usage-environment",
        )
    except ValueError as error:
        print("SUCCESS: FEAT-BRK-08 live isolation completed")
        print(f"DATA: blocked={type(error).__name__}")


def main() -> None:
    """Run environment-guard evidence.

    Returns:
        None.
    """
    fr_brokers_139_150_environment_guard()


if __name__ == "__main__":
    main()
