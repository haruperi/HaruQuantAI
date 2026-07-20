"""Secret-safe support for standalone Brokers usage programs."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.brokers import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
    BrokerResult,
)
from pydantic import SecretStr


def unavailable_capabilities() -> dict[BrokerCapabilityId, BrokerCapability]:
    """Return a complete fail-closed capability map for offline examples."""
    return {
        operation: BrokerCapability(
            capability=operation,
            implementation_status="IMPLEMENTED",
            availability="UNAVAILABLE",
            access_mode="READ",
            requirement="NONE",
            verification_status="NOT_TESTED",
            execution_model="OFFLINE_USAGE",
            reason="offline usage prevents provider side effects",
        )
        for operation in BrokerCapabilityId
    }


def config(broker_id: BrokerId) -> BrokerConnectionConfig:
    """Build one bounded, secret-safe provider configuration."""
    environment = {
        BrokerId.MT5: BrokerEnvironment.DEMO,
        BrokerId.CTRADER: BrokerEnvironment.DEMO,
        BrokerId.BINANCE_SPOT: BrokerEnvironment.TESTNET,
        BrokerId.DUKASCOPY: BrokerEnvironment.SANDBOX,
        BrokerId.YAHOO: BrokerEnvironment.SANDBOX,
    }[broker_id]
    credentials: dict[str, SecretStr] | None = None
    account_reference: str | None = None
    probe_symbol: str | None = None
    if broker_id == BrokerId.MT5:
        account_reference = "100001"
        credentials = {
            "login": SecretStr(account_reference),
            "password": SecretStr("offline-placeholder"),
            "server": SecretStr("Offline-Demo"),
        }
    elif broker_id == BrokerId.CTRADER:
        account_reference = "100001"
        credentials = {
            "client_id": SecretStr("offline-client"),
            "client_secret": SecretStr("offline-secret"),
            "access_token": SecretStr("offline-token"),
            "account_id": SecretStr(account_reference),
        }
    elif broker_id == BrokerId.BINANCE_SPOT:
        credentials = {
            "api_key": SecretStr("offline-key"),
            "api_secret": SecretStr("offline-secret"),
        }
    elif broker_id == BrokerId.YAHOO:
        probe_symbol = "EURUSD=X"
    return BrokerConnectionConfig(
        broker_id=broker_id,
        environment=environment,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=4,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        account_reference=account_reference,
        credentials=credentials,
        probe_symbol=probe_symbol,
    )


def show(label: str, result: BrokerResult[object]) -> None:
    """Print bounded result metadata without provider payloads or secrets."""
    print(label, result.status, result.operation.value)
