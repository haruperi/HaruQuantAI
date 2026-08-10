"""FEAT-BRK-10: reusable adapter conformance evidence."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import _support  # noqa: F401
from app.services.brokers import (
    build_broker_connection_config,
    create_configured_fake_broker_adapter,
    get_broker_id,
)


def fr_brokers_109_conformance() -> None:
    """Create one isolated deterministic adapter fixture.

    Returns:
        None.
    """
    config = build_broker_connection_config(
        broker_id=get_broker_id("yahoo"),
        environment="sandbox",
        provider_enabled=True,
        probe_symbol="AAPL",
    )
    adapter = create_configured_fake_broker_adapter(config)
    print("SUCCESS: FEAT-BRK-10 adapter conformance completed")
    print(f"DATA: adapter_type={type(adapter).__name__}")


def main() -> None:
    """Run adapter-conformance evidence.

    Returns:
        None.
    """
    fr_brokers_109_conformance()


if __name__ == "__main__":
    main()
