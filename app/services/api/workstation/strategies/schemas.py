"""Strategy gateway request schemas."""

from collections.abc import Mapping
from typing import Literal

from app.services.api.contracts.models import _BaseApiContract


class StrategyRegistrationRequestModel(_BaseApiContract):
    """Serialized API projection of one Strategy registration command.

    Strategy owns the registration schema and its validation policy. The gateway
    forwards the caller payload to Strategy's package-root factory unchanged and
    never supplies, defaults, or repairs a field.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.strategy_registration_request.v1"] = (
        "api.strategy_registration_request.v1"
    )
    payload: Mapping[str, object]


class StrategyParameterUpdateRequestModel(_BaseApiContract):
    """Serialized API projection of one Strategy parameter update command."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.strategy_parameter_update_request.v1"] = (
        "api.strategy_parameter_update_request.v1"
    )
    payload: Mapping[str, object]


__all__ = (
    "StrategyParameterUpdateRequestModel",
    "StrategyRegistrationRequestModel",
)
