"""Private package-wide Agentic configuration.

Approved root-private package infrastructure. No other Agentic module reads an
environment file or the process environment; every module consumes a resolved
`AgenticSettings` value.

Agentic is disabled by default. Enabling it requires a mandate path and a
versioned limits profile, so an enabled deployment can never fall back on a
hidden default that widens authority.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Self

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from app.utils import get_logger

logger = get_logger(__name__)


class AgenticSettings(BaseSettings):
    """Immutable Agentic-owned settings resolved from explicit or process values.

    Attributes:
        agentic_enabled: Master enablement for new Agentic work.
        agentic_mandate_path: Signed firm-mandate location; required when enabled.
        agentic_model_profiles: Evaluated provider-neutral model-profile IDs.
        agentic_limits_profile: Versioned limits-profile ID; required when enabled.
    """

    model_config = SettingsConfigDict(
        env_ignore_empty=True,
        case_sensitive=False,
        extra="ignore",
        frozen=True,
    )

    agentic_enabled: bool = False
    agentic_mandate_path: Path | None = None
    agentic_model_profiles: Annotated[tuple[str, ...], NoDecode] = ()
    agentic_limits_profile: str | None = None

    @field_validator("agentic_model_profiles", mode="before")
    @classmethod
    def _decode_model_profiles(cls, value: object) -> object:
        """Decode a comma-separated profile list without accepting blanks.

        Args:
            value: Candidate profile declaration.

        Returns:
            Ordered profile identifiers.

        Raises:
            ValueError: If a declared profile identifier is blank.
        """
        logger.debug("Decoding the Agentic model-profile setting")
        if not isinstance(value, str):
            return value
        entries = tuple(entry.strip() for entry in value.split(",") if entry.strip())
        if not entries:
            message = "agentic_model_profiles must not be blank when provided"
            raise ValueError(message)
        return entries

    @field_validator("agentic_model_profiles")
    @classmethod
    def _validate_model_profiles(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Reject duplicate or untrimmed model-profile identifiers.

        Args:
            value: Candidate profile identifiers.

        Returns:
            Validated profile identifiers.

        Raises:
            ValueError: If an identifier is untrimmed or duplicated.
        """
        logger.debug("Validating declared Agentic model profiles")
        for entry in value:
            if not entry or entry != entry.strip():
                message = "agentic_model_profiles entries must be non-empty trimmed"
                raise ValueError(message)
        if len(set(value)) != len(value):
            message = "agentic_model_profiles must not repeat a profile identifier"
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def _validate_enabled_requirements(self) -> Self:
        """Require the complete governed configuration whenever Agentic is enabled.

        Returns:
            The validated settings.

        Raises:
            ValueError: If an enabled deployment is missing required configuration.
        """
        if not self.agentic_enabled:
            return self
        logger.debug("Validating enabled Agentic configuration completeness")
        if self.agentic_mandate_path is None:
            message = "agentic_mandate_path is required when Agentic is enabled"
            raise ValueError(message)
        if self.agentic_limits_profile is None:
            message = "agentic_limits_profile is required when Agentic is enabled"
            raise ValueError(message)
        if not self.agentic_model_profiles:
            message = "agentic_model_profiles is required when Agentic is enabled"
            raise ValueError(message)
        return self


def get_agentic_settings(
    explicit_values: dict[str, object] | None = None,
) -> AgenticSettings:
    """Resolve immutable Agentic settings.

    Args:
        explicit_values: Optional exact settings overriding process values.

    Returns:
        Validated immutable Agentic settings.
    """
    logger.debug("Loading Agentic settings")
    if explicit_values is None:
        return AgenticSettings()
    return AgenticSettings.model_validate(explicit_values)
