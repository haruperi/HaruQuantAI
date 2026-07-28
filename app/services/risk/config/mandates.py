"""Immutable firm-mandate contracts and bounded loading."""

from __future__ import annotations

import hashlib
import re
from datetime import date
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml
from pydantic import BaseModel, ConfigDict, model_validator

from app.services.risk.contracts import RiskDomainError, RiskErrorCode
from app.services.risk.contracts.responses import guard_risk_boundary
from app.utils import get_logger

RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)

_HASH_PATTERN = re.compile(r"(?:sha256:)?[0-9a-f]{64}\Z")
_CURRENCY_CODE_LENGTH = 3


class DrawdownMode(StrEnum):
    """Supported firm drawdown-floor behaviours."""

    STATIC = "static"
    TRAILING_EOD = "trailing_eod"
    TRAILING_INTRADAY = "trailing_intraday"


class LossReferenceBasis(StrEnum):
    """Supported loss-reference balances."""

    INITIAL_BALANCE = "initial_balance"
    CURRENT_BALANCE = "current_balance"
    EQUITY = "equity"
    DAY_START = "day_start"
    INCEPTION = "inception"


class _MandateModel(BaseModel):
    """Strict immutable base for mandate configuration."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        allow_inf_nan=False,
        validate_default=True,
    )


class ProfitTarget(_MandateModel):
    """Profit-target rule expressed as a ratio or absolute amount."""

    type: Literal["percent_of_initial", "absolute"]
    value: Decimal | None = None
    value_absolute: Decimal | None = None

    @model_validator(mode="after")
    def _validate_target(self) -> ProfitTarget:
        """Require exactly one finite target representation.

        Returns:
            The validated profit-target model.

        Raises:
            ValueError: If the target representation is incomplete or conflicting.
        """
        if (self.value is None) == (self.value_absolute is None):
            raise ValueError("profit target requires exactly one value")
        if self.type == "percent_of_initial" and self.value is None:
            raise ValueError("percent target requires value")
        if self.type == "absolute" and self.value_absolute is None:
            raise ValueError("absolute target requires value_absolute")
        return self


class DailyLossRule(_MandateModel):
    """Daily loss rule and server reset boundary."""

    basis: Literal["initial_balance", "current_balance", "equity"]
    value: Decimal | None = None
    value_absolute: Decimal | None = None
    includes_unrealised: bool
    reset_time: str
    reset_tz: str

    @model_validator(mode="after")
    def _validate_rule(self) -> DailyLossRule:
        """Validate the loss representation and reset timezone.

        Returns:
            The validated daily-loss model.

        Raises:
            ValueError: If the loss representation or reset timezone is invalid.
        """
        if (self.value is None) == (self.value_absolute is None):
            raise ValueError("daily loss requires exactly one value")
        if not self.reset_time.strip():
            raise ValueError("daily loss reset time is required")
        try:
            ZoneInfo(self.reset_tz)
        except ZoneInfoNotFoundError as error:
            raise ValueError("daily loss reset timezone is unknown") from error
        return self


class DrawdownRule(_MandateModel):
    """Drawdown-floor rule and evidence requirements."""

    mode: DrawdownMode
    basis: Literal["initial_balance"]
    value: Decimal | None = None
    value_absolute: Decimal | None = None
    trails_on_unrealised: bool
    trail_stops_at_initial: bool
    eod_snapshot_time: str | None = None
    eod_snapshot_tz: str | None = None

    @model_validator(mode="after")
    def _validate_rule(self) -> DrawdownRule:
        """Validate the drawdown mode-specific requirements.

        Returns:
            The validated drawdown model.

        Raises:
            ValueError: If the drawdown representation or mode evidence is invalid.
        """
        if (self.value is None) == (self.value_absolute is None):
            raise ValueError("drawdown requires exactly one value")
        if self.mode is DrawdownMode.TRAILING_EOD:
            if not self.eod_snapshot_time or not self.eod_snapshot_tz:
                raise ValueError("trailing_eod requires snapshot time and timezone")
            try:
                ZoneInfo(self.eod_snapshot_tz)
            except ZoneInfoNotFoundError as error:
                raise ValueError("drawdown snapshot timezone is unknown") from error
        elif self.eod_snapshot_time is not None or self.eod_snapshot_tz is not None:
            raise ValueError("eod snapshot settings only apply to trailing_eod")
        if (
            self.mode is DrawdownMode.TRAILING_INTRADAY
            and not self.trails_on_unrealised
        ):
            raise ValueError("trailing_intraday must trail unrealised equity")
        return self


class ConsistencyRule(_MandateModel):
    """Optional single-day profit-share rule."""

    type: Literal["max_single_day_share_of_profit"]
    value: Decimal
    evaluated: Literal["retrospective"]
    applies_in_phase: tuple[str, ...]


class FirmMandate(_MandateModel):
    """Immutable per-account firm terms and risk mandate."""

    account_id: str
    mandate_version: str
    firm: str
    model: Literal["fx_cfd", "futures"]
    phase: Literal["evaluation_p1", "evaluation_p2", "funded"]
    initial_balance: Decimal
    currency: str
    terms_url: str
    terms_accessed: date
    terms_source_hash: str
    verified: bool
    profit_target: ProfitTarget
    daily_loss: DailyLossRule
    max_drawdown: DrawdownRule
    consistency_rule: ConsistencyRule | None = None

    @model_validator(mode="after")
    def _validate_mandate(self) -> FirmMandate:
        """Validate identity, monetary values, and terms provenance.

        Returns:
            The validated immutable mandate.

        Raises:
            ValueError: If identity, balance, currency, or terms hash is invalid.
        """
        for name in ("account_id", "mandate_version", "firm", "currency", "terms_url"):
            if not getattr(self, name).strip():
                required_name = name
                message = f"{required_name} is required"
                raise ValueError(message)
        if self.initial_balance <= 0:
            raise ValueError("initial balance must be positive")
        if (
            len(self.currency) != _CURRENCY_CODE_LENGTH
            or self.currency != self.currency.upper()
        ):
            raise ValueError("currency must be three uppercase letters")
        if _HASH_PATTERN.fullmatch(self.terms_source_hash) is None:
            raise ValueError("terms source hash must be SHA-256")
        return self


def _hash_without_prefix(value: str) -> str:
    """Normalize a mandate hash for comparison.

    Args:
        value: Hash with or without a ``sha256:`` prefix.

    Returns:
        Lowercase-compatible hexadecimal hash body.
    """
    return value.removeprefix("sha256:")


def _mandate_path(root: Path, account_id: str, suffix: str) -> Path:
    """Resolve one exact account-scoped file beneath the mandate root.

    Args:
        root: Bounded mandate directory.
        account_id: Account file stem.
        suffix: Required file suffix.

    Returns:
        Existing account-scoped file path.

    Raises:
        ValueError: If the file escapes the root or does not exist.
    """
    resolved_root = root.resolve(strict=True)
    candidate = (resolved_root / f"{account_id}{suffix}").resolve(strict=True)
    if candidate.parent != resolved_root or not candidate.is_file():
        raise ValueError("mandate file is outside the bounded root")
    return candidate


def _load_firm_mandate(account_id: str, config_root: Path) -> FirmMandate:
    """Load and verify one account mandate before boundary normalization.

    Args:
        account_id: Account identifier selecting the mandate files.
        config_root: Bounded directory containing the mandate files.

    Returns:
        Verified immutable mandate.

    Raises:
        TypeError: If the YAML document is not a mapping.
        ValueError: If identity, files, hash, or verification is invalid.
    """
    if not account_id or account_id != account_id.strip():
        raise ValueError("account identifier is invalid")
    document_path = _mandate_path(config_root, account_id, ".yaml")
    archive_path = _mandate_path(config_root, account_id, ".terms")
    payload = yaml.safe_load(document_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("mandate document must be a mapping")
    if set(payload) == {"firm_mandate"}:
        payload = payload["firm_mandate"]
    if not isinstance(payload, dict):
        raise TypeError("firm_mandate must be a mapping")
    mandate = FirmMandate.model_validate(payload)
    archived_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    if archived_hash != _hash_without_prefix(mandate.terms_source_hash):
        raise ValueError("archived terms hash does not match mandate")
    if not mandate.verified:
        raise ValueError("mandate is unverified")
    return mandate


@guard_risk_boundary(risk_level="medium", read_only=True)
def load_firm_mandate(account_id: str, config_root: Path) -> FirmMandate:
    """Load one verified firm mandate from a bounded configuration root.

    Args:
        account_id: Account identifier selecting the YAML and archive pair.
        config_root: Directory containing only the account mandate files.

    Returns:
        Verified immutable mandate.

    Raises:
        RiskDomainError: If the mandate, archive, or verification state is invalid.
    """
    logger.info("Loading verified firm mandate for account: %s", account_id)
    try:
        return _load_firm_mandate(account_id, config_root)
    except (OSError, TypeError, ValueError, yaml.YAMLError) as error:
        logger.error("Firm mandate load failed closed: %s", type(error).__name__)
        raise RiskDomainError(
            RiskErrorCode.INVALID_RISK_CONFIG,
            "firm mandate load or verification failed",
        ) from error


__all__ = [
    "ConsistencyRule",
    "DailyLossRule",
    "DrawdownMode",
    "DrawdownRule",
    "FirmMandate",
    "LossReferenceBasis",
    "ProfitTarget",
    "load_firm_mandate",
]
