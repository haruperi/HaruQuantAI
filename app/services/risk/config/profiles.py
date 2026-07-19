"""Strict Risk configuration profiles, bounded loading, and stable hashing."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
    field_serializer,
    field_validator,
    model_validator,
)

from app.services.risk.contracts import RiskDomainError, RiskErrorCode
from app.utils import logger

_HASH_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_PROFILES = frozenset({"research", "simulation", "paper", "live"})
_MAX_SCENARIOS = 100
_MAX_SCENARIO_POSITIONS = 500
_DECIMAL_FIELDS = frozenset(
    {
        "clock_skew_tolerance_seconds",
        "var_confidence",
        "max_correlation",
        "fractional_kelly_multiplier",
        "correlation_size_penalty",
        "max_daily_loss",
        "max_total_loss",
        "max_drawdown",
        "max_historical_var_ratio",
        "max_historical_cvar_ratio",
        "max_symbol_concentration",
        "max_dimension_concentration",
        "monthly_target",
        "max_margin_utilization",
        "max_effective_leverage",
        "audit_timeout_seconds",
        "approval_token_ttl_seconds",
        "token_state_timeout_seconds",
        "decision_ttl_seconds",
        "in_flight_tolerance",
        "in_flight_grace_seconds",
        "report_timeout_seconds",
    }
)
_DECIMAL_MAPPING_FIELDS = frozenset(
    {
        "max_spread",
        "allocation_caps",
        "regime_thresholds",
        "regime_modifiers",
        "dependency_timeouts_seconds",
    }
)


def _utc(value: datetime) -> datetime:
    """Require an aware UTC timestamp.

    Args:
        value: Timestamp to validate.

    Returns:
        Validated timestamp.

    Raises:
        ValueError: If the timestamp is not aware UTC.
    """
    logger.debug("Validating Risk configuration UTC timestamp")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be aware UTC")
    return value


def _text(value: str) -> str:
    """Require non-empty trimmed configuration text.

    Args:
        value: Text to validate.

    Returns:
        Validated text.

    Raises:
        ValueError: If text is empty or untrimmed.
    """
    logger.debug("Validating Risk configuration text")
    if not value or value != value.strip():
        raise ValueError("value must be non-empty trimmed text")
    return value


def _finite(value: Decimal) -> Decimal:
    """Require a finite Decimal.

    Args:
        value: Decimal to validate.

    Returns:
        Validated value.

    Raises:
        ValueError: If the value is non-finite.
    """
    logger.debug("Validating finite Risk configuration Decimal")
    if not value.is_finite():
        raise ValueError("configuration Decimal must be finite")
    return value


def _decimal_mapping(value: Mapping[str, Decimal]) -> Mapping[str, Decimal]:
    """Validate and freeze a Decimal mapping.

    Args:
        value: Mapping to validate.

    Returns:
        Immutable validated mapping.
    """
    logger.debug("Freezing Risk configuration Decimal mapping")
    return MappingProxyType({_text(key): _finite(item) for key, item in value.items()})


def _coerce_decimal(value: object) -> Decimal:
    """Convert one YAML scalar to an exact finite Decimal.

    Args:
        value: YAML scalar.

    Returns:
        Exact finite Decimal.

    Raises:
        TypeError: If the scalar has an unsupported type.
        ValueError: If the scalar is not a supported numeric representation.
    """
    logger.debug("Converting YAML numeric scalar to Decimal")
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise TypeError("Decimal YAML value is invalid")
    try:
        return _finite(Decimal(str(value)))
    except InvalidOperation as error:
        raise ValueError("Decimal YAML value is invalid") from error


def _coerce_yaml_values(payload: Mapping[str, object]) -> dict[str, object]:
    """Convert only schema-declared YAML Decimal fields.

    Args:
        payload: Loaded YAML mapping.

    Returns:
        Copy with exact Decimal values.

    Raises:
        TypeError: If a declared Decimal mapping has invalid structure.
    """
    logger.debug("Normalizing schema-declared Risk YAML numeric fields")
    normalized = dict(payload)
    for field_name in _DECIMAL_FIELDS:
        value = normalized.get(field_name)
        if value is not None:
            normalized[field_name] = _coerce_decimal(value)
    for field_name in _DECIMAL_MAPPING_FIELDS:
        value = normalized.get(field_name)
        if value is None:
            continue
        if not isinstance(value, Mapping):
            raise TypeError("Decimal YAML mapping is invalid")
        normalized[field_name] = {
            str(key): _coerce_decimal(item) for key, item in value.items()
        }
    for field_name in (
        "kill_switch_activation_permissions",
        "kill_switch_clearance_permissions",
    ):
        value = normalized.get(field_name)
        if isinstance(value, list):
            normalized[field_name] = tuple(value)
    for field_name in ("compatible_config_hashes", "crisis_windows_utc"):
        value = normalized.get(field_name)
        if isinstance(value, Mapping):
            normalized[field_name] = {
                str(key): tuple(item) if isinstance(item, list) else item
                for key, item in value.items()
            }
    return normalized


class RiskConfig(BaseModel):
    """Frozen authoritative Risk policy configuration version 1."""

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        frozen=True,
        allow_inf_nan=False,
        arbitrary_types_allowed=True,
        validate_default=True,
    )

    schema_version: Literal["v1"] = "v1"
    profile: Literal["research", "simulation", "paper", "live"]
    execution_route: Literal["none", "sim", "paper", "live"]
    policy_version: str
    base_currency: str
    decimal_rounding: Literal["ROUND_HALF_EVEN"] = "ROUND_HALF_EVEN"
    pending_order_exposure_policy: Literal["include_full_remaining_exposure", "block"]
    evidence_max_age_seconds: Mapping[str, int]
    clock_skew_tolerance_seconds: Decimal | None = None
    audit_persistence_required: bool = True
    var_method: Literal["historical"] = "historical"
    var_confidence: Decimal = Decimal("0.95")
    var_min_observations: int | None = None
    var_lookback: int | None = None
    max_correlation: Decimal = Decimal("0.50")
    psd_policy: Literal["reject"] = "reject"
    min_kelly_trades: int = 30
    fractional_kelly_multiplier: Decimal | None = None
    allow_full_kelly: bool = False
    kelly_insufficient_evidence_mode: (
        Literal["reject", "fixed_risk_fallback"] | None
    ) = None
    correlation_size_penalty: Decimal | None = None
    max_daily_loss: Decimal = Decimal("0.05")
    max_total_loss: Decimal = Decimal("0.10")
    max_drawdown: Decimal = Decimal("0.10")
    max_historical_var_ratio: Decimal = Decimal("0.02")
    max_historical_cvar_ratio: Decimal = Decimal("0.03")
    max_symbol_concentration: Decimal = Decimal("0.10")
    max_dimension_concentration: Decimal = Decimal("0.25")
    monthly_target: Decimal | None = Decimal("0.10")
    max_margin_utilization: Decimal | None = Decimal("0.50")
    max_effective_leverage: Decimal | None = Decimal(10)
    max_spread: Mapping[str, Decimal] = {}
    news_blackout_before_minutes: int = 10
    news_blackout_after_minutes: int = 10
    missing_calendar_mode: (
        Literal["ignore", "warn", "needs_more_evidence", "block"] | None
    ) = None
    session_timezone: str | None = None
    allowed_session_states: tuple[str, ...] = ("open",)
    blocked_calendar_states: tuple[str, ...] = (
        "blackout_before",
        "event",
        "blackout_after",
    )
    allocation_caps: Mapping[str, Decimal] = {}
    regime_assessment_enabled: bool
    regime_thresholds: Mapping[str, Decimal] = {
        "volatility_elevated": Decimal("0.02"),
        "volatility_high": Decimal("0.04"),
        "correlation_elevated": Decimal("0.50"),
        "correlation_high": Decimal("0.75"),
        "drawdown_elevated": Decimal("0.05"),
        "drawdown_high": Decimal("0.10"),
    }
    regime_modifiers: Mapping[str, Decimal] = {
        "elevated": Decimal("0.75"),
        "high": Decimal("0.50"),
    }
    stressed_lookback_days: int | None = None
    crisis_windows_utc: Mapping[str, tuple[datetime, datetime]] = {}
    audit_hash_algorithm: Literal["sha256"] = "sha256"
    audit_genesis_hash: str = "0" * 64
    audit_timeout_seconds: Decimal | None = None
    audit_retry_attempts: int = 0
    approval_token_ttl_seconds: Decimal
    approval_signing_key_ref: str
    approval_signing_algorithm: Literal["hmac-sha256"] = "hmac-sha256"
    token_state_timeout_seconds: Decimal | None = None
    compatible_config_hashes: Mapping[str, tuple[str, ...]] = {}
    decision_ttl_seconds: Decimal
    in_flight_tolerance: Decimal | None = None
    in_flight_grace_seconds: Decimal | None = None
    double_spend_owner: Literal["risk_store", "capacity_guard"] | None = None
    kill_switch_activation_permissions: tuple[str, ...]
    kill_switch_clearance_permissions: tuple[str, ...]
    max_scenarios_per_run: int = 100
    max_positions_per_scenario_run: int = 500
    risk_report_format: Literal["markdown", "json"] = "markdown"
    report_timeout_seconds: Decimal
    dependency_timeouts_seconds: Mapping[str, Decimal] = {}

    @field_validator("policy_version", "base_currency", "approval_signing_key_ref")
    @classmethod
    def _validate_required_text(cls, value: str) -> str:
        """Validate required textual policy fields.

        Args:
            value: Text to validate.

        Returns:
            Validated text.
        """
        logger.debug("Validating required RiskConfig text")
        return _text(value)

    @field_validator("session_timezone")
    @classmethod
    def _validate_timezone(cls, value: str | None) -> str | None:
        """Validate an optional IANA timezone name.

        Args:
            value: Optional timezone.

        Returns:
            Validated timezone.

        Raises:
            ValueError: If the timezone is unknown.
        """
        logger.debug("Validating RiskConfig session timezone")
        if value is None:
            return None
        checked = _text(value)
        try:
            ZoneInfo(checked)
        except ZoneInfoNotFoundError as error:
            raise ValueError("session timezone is unknown") from error
        return checked

    @field_validator(
        "clock_skew_tolerance_seconds",
        "var_confidence",
        "max_correlation",
        "fractional_kelly_multiplier",
        "correlation_size_penalty",
        "max_daily_loss",
        "max_total_loss",
        "max_drawdown",
        "max_historical_var_ratio",
        "max_historical_cvar_ratio",
        "max_symbol_concentration",
        "max_dimension_concentration",
        "monthly_target",
        "max_margin_utilization",
        "max_effective_leverage",
        "audit_timeout_seconds",
        "approval_token_ttl_seconds",
        "token_state_timeout_seconds",
        "decision_ttl_seconds",
        "in_flight_tolerance",
        "in_flight_grace_seconds",
        "report_timeout_seconds",
    )
    @classmethod
    def _validate_decimal(cls, value: Decimal | None) -> Decimal | None:
        """Validate every scalar Decimal as finite.

        Args:
            value: Optional Decimal.

        Returns:
            Validated value.
        """
        logger.debug("Validating scalar RiskConfig Decimal")
        return None if value is None else _finite(value)

    @field_validator(
        "max_spread",
        "allocation_caps",
        "regime_thresholds",
        "regime_modifiers",
        "dependency_timeouts_seconds",
        mode="after",
    )
    @classmethod
    def _freeze_decimal_mappings(
        cls, value: Mapping[str, Decimal]
    ) -> Mapping[str, Decimal]:
        """Validate and freeze mapped Decimal settings.

        Args:
            value: Mapping to validate.

        Returns:
            Immutable mapping.
        """
        logger.debug("Validating mapped RiskConfig Decimals")
        return _decimal_mapping(value)

    @field_validator("evidence_max_age_seconds", mode="after")
    @classmethod
    def _validate_evidence_ages(cls, value: Mapping[str, int]) -> Mapping[str, int]:
        """Validate and freeze positive evidence freshness bounds.

        Args:
            value: Evidence age mapping.

        Returns:
            Immutable mapping.

        Raises:
            ValueError: If the mapping is empty or contains a non-positive age.
        """
        logger.debug("Validating RiskConfig evidence freshness bounds")
        if not value or any(age <= 0 for age in value.values()):
            raise ValueError("evidence ages must be non-empty and positive")
        return MappingProxyType({_text(key): age for key, age in value.items()})

    @field_validator(
        "allowed_session_states",
        "blocked_calendar_states",
        "kill_switch_activation_permissions",
        "kill_switch_clearance_permissions",
    )
    @classmethod
    def _validate_text_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate a non-empty unique policy text tuple.

        Args:
            value: Permission names.

        Returns:
            Validated permissions.

        Raises:
            ValueError: If values are empty or duplicated.
        """
        logger.debug("Validating RiskConfig policy text tuple")
        checked = tuple(_text(item) for item in value)
        if not checked or len(set(checked)) != len(checked):
            raise ValueError("policy values must be non-empty and unique")
        return checked

    @field_validator("crisis_windows_utc", mode="after")
    @classmethod
    def _validate_crisis_windows(
        cls, value: Mapping[str, tuple[datetime, datetime]]
    ) -> Mapping[str, tuple[datetime, datetime]]:
        """Validate and freeze ordered UTC crisis windows.

        Args:
            value: Named crisis windows.

        Returns:
            Immutable validated windows.

        Raises:
            ValueError: If a window is unordered.
        """
        logger.debug("Validating RiskConfig crisis windows")
        checked: dict[str, tuple[datetime, datetime]] = {}
        for key, (start, end) in value.items():
            checked_start, checked_end = _utc(start), _utc(end)
            if checked_end <= checked_start:
                raise ValueError("crisis window end must follow start")
            checked[_text(key)] = (checked_start, checked_end)
        return MappingProxyType(checked)

    @field_validator("compatible_config_hashes", mode="after")
    @classmethod
    def _validate_hashes(
        cls, value: Mapping[str, tuple[str, ...]]
    ) -> Mapping[str, tuple[str, ...]]:
        """Validate explicit compatible SHA-256 hash pairs.

        Args:
            value: Current-hash to compatible-hash mapping.

        Returns:
            Immutable validated mapping.

        Raises:
            ValueError: If a hash is malformed or duplicated.
        """
        logger.debug("Validating RiskConfig compatible hash pairs")
        checked: dict[str, tuple[str, ...]] = {}
        for key, hashes in value.items():
            if _HASH_PATTERN.fullmatch(key) is None:
                raise ValueError("compatible config hash is invalid")
            if len(set(hashes)) != len(hashes) or any(
                _HASH_PATTERN.fullmatch(item) is None for item in hashes
            ):
                raise ValueError("compatible config hash list is invalid")
            checked[key] = hashes
        return MappingProxyType(checked)

    @field_serializer(
        "evidence_max_age_seconds",
        "max_spread",
        "allocation_caps",
        "regime_thresholds",
        "regime_modifiers",
        "crisis_windows_utc",
        "compatible_config_hashes",
        "dependency_timeouts_seconds",
        when_used="json",
    )
    def _serialize_mapping(self, value: Mapping[str, object]) -> dict[str, object]:
        """Serialize an immutable configuration mapping to canonical JSON input.

        Args:
            value: Configuration mapping.

        Returns:
            Ordinary mapping for Pydantic JSON serialization.
        """
        logger.debug("Serializing immutable RiskConfig mapping")
        return dict(value)

    @model_validator(mode="after")
    def _validate_policy(self) -> RiskConfig:
        """Validate cross-field Risk policy invariants.

        Returns:
            Validated configuration.

        Raises:
            ValueError: If profile safety or policy relationships conflict.
        """
        logger.info("Validating complete RiskConfig policy invariants")
        expected_route = {
            "research": "none",
            "simulation": "sim",
            "paper": "paper",
            "live": "live",
        }[self.profile]
        if self.execution_route != expected_route:
            raise ValueError("profile and execution route are incompatible")
        self._validate_numeric_policy()
        self._validate_capability_policy()
        self._validate_live_policy()
        return self

    def _validate_numeric_policy(self) -> None:
        """Validate numeric ranges and ordered bounds.

        Raises:
            ValueError: If a numeric policy value is outside its range.
        """
        logger.debug("Validating RiskConfig numeric policy ranges")
        self._validate_ratio_policy()
        self._validate_timeout_policy()

    def _validate_ratio_policy(self) -> None:
        """Validate ratios, caps, spreads, and ordered loss limits.

        Raises:
            ValueError: If a ratio or ordered limit is invalid.
        """
        logger.debug("Validating RiskConfig ratio policy")
        if not Decimal(0) < self.var_confidence < Decimal(1):
            raise ValueError("var confidence must be between zero and one")
        if not Decimal(0) <= self.max_correlation <= Decimal(1):
            raise ValueError("maximum correlation must be between zero and one")
        if self.max_daily_loss <= 0 or self.max_total_loss < self.max_daily_loss:
            raise ValueError("loss limits are invalid")
        positive_ratios = (
            self.fractional_kelly_multiplier,
            self.correlation_size_penalty,
            self.max_drawdown,
            self.max_historical_var_ratio,
            self.max_historical_cvar_ratio,
            self.max_symbol_concentration,
            self.max_dimension_concentration,
            self.max_margin_utilization,
        )
        if any(
            value is not None and not Decimal(0) < value <= Decimal(1)
            for value in positive_ratios
        ):
            raise ValueError("ratio setting must be in (0, 1]")
        if self.max_historical_cvar_ratio < self.max_historical_var_ratio:
            raise ValueError("historical CVaR limit cannot be below VaR limit")
        if any(value <= 0 or value > 1 for value in self.allocation_caps.values()):
            raise ValueError("allocation caps must be positive ratios")
        if any(value < 0 for value in self.max_spread.values()):
            raise ValueError("maximum spreads must be non-negative")
        if any(value <= 0 for value in self.dependency_timeouts_seconds.values()):
            raise ValueError("dependency timeouts must be positive")
        if (
            self.clock_skew_tolerance_seconds is not None
            and self.clock_skew_tolerance_seconds < 0
        ):
            raise ValueError("clock skew tolerance must be non-negative")

    def _validate_timeout_policy(self) -> None:
        """Validate required and conditional timeout values.

        Raises:
            ValueError: If a timeout or tolerance is outside its range.
        """
        logger.debug("Validating RiskConfig timeout policy")
        required_positive = (
            self.approval_token_ttl_seconds,
            self.decision_ttl_seconds,
            self.report_timeout_seconds,
        )
        if any(value <= 0 for value in required_positive):
            raise ValueError("required timeouts must be positive")
        optional_positive = (
            self.max_effective_leverage,
            self.audit_timeout_seconds,
            self.token_state_timeout_seconds,
            self.in_flight_grace_seconds,
        )
        if any(value is not None and value <= 0 for value in optional_positive):
            raise ValueError("optional positive setting is invalid")
        if self.in_flight_tolerance is not None and self.in_flight_tolerance < 0:
            raise ValueError("in-flight tolerance must be non-negative")

    def _validate_capability_policy(self) -> None:
        """Validate enabled capability requirements.

        Raises:
            ValueError: If an enabled capability lacks required policy.
        """
        logger.debug("Validating RiskConfig capability-specific policy")
        self._validate_observation_policy()
        self._validate_regime_policy()
        self._validate_bounded_counts()

    def _validate_observation_policy(self) -> None:
        """Validate VaR, Kelly, and stressed-observation policy.

        Raises:
            ValueError: If observation requirements conflict.
        """
        logger.debug("Validating RiskConfig observation policy")
        if self.var_min_observations is not None and self.var_min_observations <= 0:
            raise ValueError("minimum VaR observations must be positive")
        if self.var_lookback is not None and self.var_lookback <= 0:
            raise ValueError("VaR lookback must be positive")
        if (
            self.var_min_observations is not None
            and self.var_lookback is not None
            and self.var_lookback < self.var_min_observations
        ):
            raise ValueError("VaR lookback is below minimum observations")
        if self.min_kelly_trades <= 0:
            raise ValueError("minimum Kelly trades must be positive")
        if (
            self.kelly_insufficient_evidence_mode is not None
            and self.fractional_kelly_multiplier is None
        ):
            raise ValueError("Kelly mode requires a fractional multiplier")
        if self.stressed_lookback_days is not None and self.stressed_lookback_days <= 0:
            raise ValueError("stressed lookback must be positive")

    def _validate_regime_policy(self) -> None:
        """Validate enabled regime-assessment policy.

        Raises:
            ValueError: If enabled regime policy is incomplete or loosening.
        """
        logger.debug("Validating RiskConfig regime policy")
        if self.regime_assessment_enabled:
            required_thresholds = {
                "volatility_elevated",
                "volatility_high",
                "correlation_elevated",
                "correlation_high",
                "drawdown_elevated",
                "drawdown_high",
            }
            if set(self.regime_thresholds) != required_thresholds or set(
                self.regime_modifiers
            ) != {"elevated", "high"}:
                raise ValueError("enabled regime assessment requires complete policy")
            for dimension in ("volatility", "correlation", "drawdown"):
                elevated = self.regime_thresholds[f"{dimension}_elevated"]
                high = self.regime_thresholds[f"{dimension}_high"]
                if elevated < 0 or high < elevated:
                    raise ValueError("regime thresholds must be ordered")
            if any(
                not Decimal(0) < value <= Decimal(1)
                for value in self.regime_modifiers.values()
            ):
                raise ValueError("regime modifiers may only tighten")
            if self.regime_modifiers["high"] > self.regime_modifiers["elevated"]:
                raise ValueError("high regime modifier must be at least as strict")
            if self.profile == "live" and (
                self.stressed_lookback_days is None or not self.crisis_windows_utc
            ):
                raise ValueError("live regime assessment requires stressed policy")

    def _validate_bounded_counts(self) -> None:
        """Validate non-negative counters and bounded workload sizes.

        Raises:
            ValueError: If a count is outside its V1 bound.
        """
        logger.debug("Validating RiskConfig bounded counters")
        if (
            self.news_blackout_before_minutes < 0
            or self.news_blackout_after_minutes < 0
        ):
            raise ValueError("news blackout bounds must be non-negative")
        if self.audit_retry_attempts < 0:
            raise ValueError("audit retry attempts must be non-negative")
        if not 0 < self.max_scenarios_per_run <= _MAX_SCENARIOS:
            raise ValueError("scenario limit is outside V1 bounds")
        if not 0 < self.max_positions_per_scenario_run <= _MAX_SCENARIO_POSITIONS:
            raise ValueError("position scenario limit is outside V1 bounds")
        if _HASH_PATTERN.fullmatch(self.audit_genesis_hash) is None:
            raise ValueError("audit genesis hash must be lowercase SHA-256 hex")

    def _validate_live_policy(self) -> None:
        """Require all unambiguous live safety values.

        Raises:
            ValueError: If a live profile omits mandatory policy.
        """
        logger.debug("Validating fail-closed live RiskConfig requirements")
        if self.profile != "live":
            return
        required = (
            self.clock_skew_tolerance_seconds,
            self.var_min_observations,
            self.max_margin_utilization,
            self.max_effective_leverage,
            self.missing_calendar_mode,
            self.audit_timeout_seconds,
            self.token_state_timeout_seconds,
            self.double_spend_owner,
        )
        if any(value is None for value in required):
            raise ValueError("live profile is missing mandatory safety policy")
        if not self.audit_persistence_required:
            raise ValueError("live profile requires durable audit persistence")


def _load_risk_config(profile: str, config_root: Path) -> RiskConfig:
    """Perform bounded profile loading before boundary error normalization.

    Args:
        profile: Approved profile name.
        config_root: Caller-supplied configuration root.

    Returns:
        Strict validated configuration.

    Raises:
        OSError: If the root or profile is unavailable.
        TypeError: If YAML structure is incompatible.
        ValueError: If the path, profile, or policy is invalid.
        ValidationError: If Pydantic validation fails.
        yaml.YAMLError: If YAML parsing fails.
    """
    logger.debug("Resolving bounded Risk configuration profile")
    if profile not in _PROFILES:
        raise ValueError("profile name is not approved")
    root = config_root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("configuration root is not a directory")
    candidate = (root / f"{profile}.yaml").resolve(strict=True)
    if candidate.parent != root or not candidate.is_file():
        raise ValueError("configuration profile escapes bounded root")
    loaded = yaml.safe_load(candidate.read_text(encoding="utf-8"))
    if not isinstance(loaded, Mapping):
        raise TypeError("configuration document must be a mapping")
    normalized = _coerce_yaml_values(loaded)
    config = RiskConfig.model_validate(normalized)
    if config.profile != profile:
        raise ValueError("selected profile does not match document")
    return config


def load_risk_config(profile: str, config_root: Path) -> RiskConfig:
    """Load one selected YAML profile from an exact bounded root.

    Args:
        profile: Approved profile name.
        config_root: Caller-supplied configuration root.

    Returns:
        Strict validated configuration.

    Raises:
        RiskDomainError: If the path, YAML, or policy is invalid.
    """
    logger.info("Loading selected bounded Risk configuration profile: %s", profile)
    try:
        return _load_risk_config(profile, config_root)
    except (OSError, TypeError, ValueError, ValidationError, yaml.YAMLError) as error:
        logger.error("Risk configuration load failed closed: %s", type(error).__name__)
        raise RiskDomainError(
            RiskErrorCode.INVALID_RISK_CONFIG,
            "profile load or validation failed",
        ) from error


def compute_config_hash(config: RiskConfig) -> str:
    """Hash canonical exact JSON serialization of one Risk configuration.

    Args:
        config: Validated Risk configuration.

    Returns:
        Lowercase SHA-256 hexadecimal digest.

    Raises:
        RiskDomainError: If canonical serialization fails.
    """
    logger.info("Computing canonical Risk configuration hash")
    try:
        payload = config.model_dump(mode="json")
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    except (TypeError, ValueError) as error:
        logger.error("Risk configuration canonicalization failed")
        raise RiskDomainError(
            RiskErrorCode.INVALID_RISK_CONFIG,
            "canonical configuration serialization failed",
        ) from error


__all__ = ["RiskConfig", "compute_config_hash", "load_risk_config"]
