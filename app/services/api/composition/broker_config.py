"""Secret-reference resolution at the Brokers composition boundary."""

from collections.abc import Mapping

from pydantic import SecretStr

from app.services.api.composition.runtime_settings import build_credential_key_set
from app.services.api.identity import get_system_settings, resolve_credential_reference
from app.services.api.workstation.settings.bootstrap import get_api_settings
from app.services.brokers import build_broker_connection_config as _build_broker_config
from app.utils import derive_stable_id, get_logger

logger = get_logger(__name__)

_PROVIDER_SETTINGS = {
    "mt5": ("MT5_ENABLED", "demo", "mt5"),
    "ctrader": ("CTRADER_ENABLED", "demo", "ctrader"),
    "binance_spot": ("BINANCE_ENABLED", "testnet", None),
    "dukascopy": ("DUKASCOPY_ENABLED", "sandbox", None),
    "yahoo": ("YAHOO_ENABLED", "sandbox", None),
}


def _enabled(value: object) -> bool:
    """Interpret one persisted provider enablement value.

    Args:
        value: Persisted system-setting value.

    Returns:
        Whether the value is the canonical enabled representation.
    """
    return str(value).strip().lower() == "true"


def _resolve_system_credentials(
    slot: str, *, request_id: str
) -> Mapping[str, SecretStr]:
    """Resolve one encrypted system credential slot for immediate composition.

    Args:
        slot: Manifest-approved system credential slot.
        request_id: Canonical request identifier.

    Returns:
        Decrypted values wrapped in secret-redacting objects.

    Raises:
        ValueError: If the external encryption key is unavailable.
        IdentityError: If the stored credential cannot be resolved safely.
    """
    reference_id = derive_stable_id("id", f"api-credential:system:{slot}")
    return resolve_credential_reference(
        f"secret://{reference_id}",
        owner_id="system",
        key_set=build_credential_key_set(get_api_settings()),
        request_id=request_id,
    )


def build_system_broker_connection_config(
    broker_id: str,
    *,
    request_id: str,
    environment: str | None = None,
) -> object:
    """Build a system Broker config from authoritative stored settings.

    Args:
        broker_id: Exact Brokers provider identifier.
        request_id: Canonical request identifier.
        environment: Explicit elected MT5 environment. Other providers retain
            their fixed non-production environment.

    Returns:
        Immutable Brokers-owned connection configuration.

    Raises:
        ValueError: If the provider is unsupported, disabled, or the requested
            environment is invalid for that provider.
        IdentityError: If required credentials cannot be resolved safely.
    """
    if broker_id not in _PROVIDER_SETTINGS:
        raise ValueError("unsupported system broker provider")
    enabled_key, default_environment, credential_slot = _PROVIDER_SETTINGS[broker_id]
    resolved_environment = environment or default_environment
    if environment is not None and broker_id != "mt5":
        raise ValueError("environment override is supported only for mt5")
    if broker_id == "mt5" and resolved_environment not in {"demo", "live"}:
        raise ValueError("mt5 system environment is invalid")
    settings_record = get_system_settings(request_id=request_id)
    if not _enabled(settings_record.settings.get(enabled_key, "false")):
        message = f"{broker_id} system provider is disabled"
        raise ValueError(message)
    credentials: Mapping[str, SecretStr] = {}
    if credential_slot is not None:
        credentials = _resolve_system_credentials(
            credential_slot,
            request_id=request_id,
        )
    account_field = {"mt5": "login", "ctrader": "account_id"}.get(broker_id)
    account_reference = (
        credentials[account_field].get_secret_value()
        if account_field is not None and account_field in credentials
        else None
    )
    probe_symbol = "AAPL" if broker_id == "yahoo" else None
    logger.info("Composing one enabled non-production system broker configuration")
    return _build_broker_config(
        broker_id=broker_id,
        environment=resolved_environment,
        account_reference=account_reference,
        credentials=credentials or None,
        provider_enabled=True,
        probe_symbol=probe_symbol,
    )


def build_broker_connection_config(
    *,
    credential_reference: str,
    owner_id: str,
    key_set: Mapping[str, bytes],
    request_id: str,
    broker_id: str,
    environment: str,
    account_reference: str | None = None,
    provider_enabled: bool = True,
) -> object:
    """Resolve an opaque credential and construct a Brokers-owned config.

    Args:
        credential_reference: UI/API-owned opaque secret reference.
        owner_id: Authenticated credential owner.
        key_set: Externally provisioned in-memory encryption keys.
        request_id: Canonical request identifier.
        broker_id: Brokers-owned provider identifier.
        environment: Brokers-owned target environment.
        account_reference: Optional non-secret account label.
        provider_enabled: Whether provider connections are enabled.

    Returns:
        Immutable Brokers-owned connection configuration.
    """
    logger.info("Resolving credential reference for Brokers composition")
    credentials = resolve_credential_reference(
        credential_reference,
        owner_id=owner_id,
        key_set=key_set,
        request_id=request_id,
    )
    return _build_broker_config(
        broker_id=broker_id,
        environment=environment,
        account_reference=account_reference,
        credentials=credentials,
        provider_enabled=provider_enabled,
    )


__all__ = (
    "build_broker_connection_config",
    "build_system_broker_connection_config",
)
