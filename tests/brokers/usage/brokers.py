"""Executable examples for the Brokers package-root public API."""

import sys
from pathlib import Path

# Add project root to path before importing local modules
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.brokers import (
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
    create_broker_adapter,
    get_broker_capability_catalogue,
    get_registered_brokers,
)


def _header(title: str) -> None:
    """Print the header for an example section.

    Args:
        title: The title of the section to display.
    """
    print(f"\n\n\n{'=' * 100}")
    print(f"\t\t{title}\t")
    print(f"{'=' * 100}\n")


_header("Example 1: Returns a list of all registered BrokerId profiles.")
brokers = get_registered_brokers()
print("Registered Brokers:", [b.value for b in brokers])

_header("Example 2: Returns the complete static capability catalogue.")
catalogue = get_broker_capability_catalogue()
print("Catalogue Broker IDs:", list(catalogue.keys()))
for cap in catalogue.get(BrokerId.YAHOO, ()):
    if cap.availability == "AVAILABLE":
        print(f"Yahoo Available Operation: {cap.capability.value}")

_header("Example 3: Creates one exact disconnected adapter instance.")
config = BrokerConnectionConfig(
    broker_id=BrokerId.YAHOO,
    environment=BrokerEnvironment.SANDBOX,
    provider_enabled=True,
    connect_timeout_sec=5.0,
    request_timeout_sec=5.0,
    transport_reconnect_max_attempts=0,
    stream_buffer_size=4,
    circuit_failure_threshold=2,
    circuit_recovery_timeout_sec=1.0,
    circuit_half_open_max_calls=1,
)
result = create_broker_adapter(BrokerId.YAHOO, config)
print("Create adapter status:", result.status)
if result.status == "success" and result.data is not None:
    print("Created adapter class:", result.data.__class__.__name__)
