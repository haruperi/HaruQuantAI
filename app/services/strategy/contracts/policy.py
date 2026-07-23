"""Explicit host-owned Strategy validation policy."""

from __future__ import annotations

from typing import Literal

from pydantic import (
    Field,
    field_validator,
)

from app.services.strategy.contracts._base import (
    _Contract,
    _text,
)
from app.utils import logger


class StrategyValidationPolicy(_Contract):
    """Explicit host-owned module and configuration validation policy."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.validation_policy.v1"] = (
        "strategy.validation_policy.v1"
    )
    policy_version: str
    approved_module_roots: tuple[str, ...]
    max_config_payload_bytes: int = Field(gt=0)
    max_config_nesting_depth: int = Field(gt=0)
    max_config_string_length: int = Field(gt=0)
    max_config_collection_items: int = Field(gt=0)

    @field_validator("policy_version")
    @classmethod
    def _validate_policy_version(cls, value: str) -> str:
        """Validate the policy version.

        Args:
            value: Version text.

        Returns:
            Validated text.
        """
        logger.debug("Validating Strategy policy version")
        return _text(value)

    @field_validator("approved_module_roots")
    @classmethod
    def _validate_roots(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate approved module roots.

        Args:
            value: Approved roots.

        Returns:
            Validated unique roots.

        Raises:
            ValueError: If roots are empty, duplicated, or malformed.
        """
        logger.debug("Validating approved Strategy module roots")
        roots = tuple(_text(root).rstrip(".") for root in value)
        if not roots or len(set(roots)) != len(roots):
            raise ValueError("approved_module_roots must be non-empty and unique")
        return roots
