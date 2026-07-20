"""Broker communication security profile contracts."""

from __future__ import annotations

from app.services.trading.config.models import TradingConfigModel
from app.utils.logger import logger
from pydantic import model_validator


class BrokerSecurityProfile(TradingConfigModel):
    """Security expectations required for live broker mutation."""

    profile_name: str
    encrypted_transport_required: bool = True
    certificate_validation_required: bool = True
    redact_logs: bool = True
    adapter_attestation: str | None = None
    compliant_adapters: frozenset[str] = frozenset()

    @model_validator(mode="after")
    def validate_profile(self) -> BrokerSecurityProfile:
        """Validate security profile shape.

        Returns:
            BrokerSecurityProfile: Validated security profile.
        """
        logger.info("Validating broker security profile {}.", self.profile_name)
        if not self.profile_name.strip():
            raise ValueError("profile_name must be non-empty.")
        return self


def validate_live_security_profile(
    *,
    profile: BrokerSecurityProfile,
    adapter_name: str,
) -> None:
    """Validate that a live mutation may use this security profile.

    Args:
        profile: Broker communication security profile.
        adapter_name: Active adapter name.

    Raises:
        ValueError: If the profile does not satisfy live mutation security
            requirements.
    """
    logger.info("Validating live security profile for adapter {}.", adapter_name)
    if not profile.encrypted_transport_required:
        raise ValueError("live mutation requires encrypted transport.")
    if not profile.certificate_validation_required:
        raise ValueError("live mutation requires certificate validation.")
    if not profile.redact_logs:
        raise ValueError("live mutation requires restricted/redacted logging.")
    if not profile.adapter_attestation:
        raise ValueError("live mutation requires adapter compliance attestation.")
    if adapter_name not in profile.compliant_adapters:
        raise ValueError("adapter is not approved by the security profile.")
