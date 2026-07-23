"""FEAT-BRK-01: discover providers, capabilities, and construct an adapter.

Exercises the genuine registry: complete profile listing without importing any
provider SDK, the complete static capability catalogue, explicit adapter
creation, and the fail-closed paths for unknown and disabled providers.
"""

import sys

from _support import config
from app.services.brokers import (
    BrokerCapabilityId,
    BrokerErrorCode,
    BrokerId,
    create_broker_adapter,
    get_broker_capability_catalogue,
    get_registered_brokers,
)


def example_listing_imports_no_provider_sdk() -> None:
    """FR-BRK-102: every registered profile is listed without an SDK import."""
    before = {
        name for name in sys.modules if name.startswith(("MetaTrader5", "binance"))
    }
    registered = get_registered_brokers()
    after = {
        name for name in sys.modules if name.startswith(("MetaTrader5", "binance"))
    }
    print("registered profiles", len(registered))
    print("provider SDKs imported by listing", len(after - before))


def example_catalogue_is_complete() -> None:
    """FR-BRK-103: one complete declaration covers every profile/operation."""
    catalogue = get_broker_capability_catalogue()
    print("catalogue profiles", len(catalogue))
    mt5 = {entry.capability: entry for entry in catalogue[BrokerId.MT5]}
    print("mt5 operations declared", len(mt5), "of", len(tuple(BrokerCapabilityId)))
    released = sum(1 for entry in mt5.values() if entry.availability == "AVAILABLE")
    writes = tuple(entry for entry in mt5.values() if entry.access_mode == "WRITE")
    print("mt5 available", released)
    print(
        "mt5 writes unavailable",
        all(entry.availability == "UNAVAILABLE" for entry in writes),
    )
    quote = mt5[BrokerCapabilityId.GET_QUOTE]
    print(
        "released read evidence",
        len(quote.verification_evidence),
        quote.verification_status,
    )


def example_explicit_creation_never_falls_back() -> None:
    """FR-BRK-101: only the exact requested profile is ever resolved."""
    created = create_broker_adapter(BrokerId.YAHOO, config(BrokerId.YAHOO))
    print("create yahoo", created.status)

    mismatched = create_broker_adapter(BrokerId.MT5, config(BrokerId.YAHOO))
    print(
        "mismatched id/config",
        mismatched.status,
        mismatched.error.code.value if mismatched.error else None,
    )


def example_disabled_provider_fails_before_import() -> None:
    """A disabled provider is rejected before any provider module is imported."""
    enabled = config(BrokerId.YAHOO)
    disabled = enabled.__class__(
        broker_id=enabled.broker_id,
        environment=enabled.environment,
        provider_enabled=False,
        connect_timeout_sec=enabled.connect_timeout_sec,
        request_timeout_sec=enabled.request_timeout_sec,
        transport_reconnect_max_attempts=enabled.transport_reconnect_max_attempts,
        stream_buffer_size=enabled.stream_buffer_size,
        circuit_failure_threshold=enabled.circuit_failure_threshold,
        circuit_recovery_timeout_sec=enabled.circuit_recovery_timeout_sec,
        circuit_half_open_max_calls=enabled.circuit_half_open_max_calls,
        probe_symbol=enabled.probe_symbol,
    )
    result = create_broker_adapter(BrokerId.YAHOO, disabled)
    print(
        "disabled provider",
        result.status,
        result.error.code.value if result.error else None,
        result.error.code is BrokerErrorCode.BROKER_CONFIGURATION_INVALID
        if result.error
        else None,
    )


def main() -> None:
    """Exercise every FEAT-BRK-01 public operation."""
    example_listing_imports_no_provider_sdk()
    example_catalogue_is_complete()
    example_explicit_creation_never_falls_back()
    example_disabled_provider_fails_before_import()


if __name__ == "__main__":
    main()
