"""Immutable evidence and snapshots consumed inside Risk."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from decimal import Decimal
from types import MappingProxyType
from typing import Literal, Protocol, runtime_checkable

from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationInfo,
    field_serializer,
    field_validator,
    model_validator,
)

from app.composition.logging import get_logger
from app.kernel.identity import validate_id
from app.services.data import (
    build_account_state_snapshot,
    build_fx_conversion_evidence,
    build_market_context_evidence,
)
from app.services.risk.contracts.enums import LimitStatus, RiskErrorCode
from app.services.risk.contracts.errors import RiskDomainError
from app.services.risk.contracts.responses import guard_risk_boundary

RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)

_CURRENCY_CODE_LENGTH = 3
_CORRELATION_PAIR_SIZE = 2


@runtime_checkable
class _AccountItemView(Protocol):
    """Structural view of one Data-owned account position or order."""

    symbol: str
    side: str
    quantity: Decimal


@runtime_checkable
class _AccountStateSnapshotView(Protocol):
    """Structural view of the Data-owned account snapshot."""

    contract_version: str
    account_id: str
    currency: str
    equity: Decimal
    margin_used: Decimal | None
    positions: tuple[_AccountItemView, ...]
    orders: tuple[_AccountItemView, ...]
    snapshot_at: datetime
    expires_at: datetime
    request_id: str

    def model_dump(
        self,
        *,
        mode: str = "python",
        warnings: bool = True,
    ) -> dict[str, object]:
        """Return the complete account snapshot payload."""
        ...


@runtime_checkable
class _FXConversionEvidenceView(Protocol):
    """Structural view of Data-owned FX conversion evidence."""

    contract_version: str
    source_currency: str
    target_currency: str
    composite_rate: Decimal
    as_of: datetime
    expires_at: datetime
    request_id: str

    def model_dump(
        self,
        *,
        mode: str = "python",
        warnings: bool = True,
    ) -> dict[str, object]:
        """Return the complete FX conversion payload."""
        ...


@runtime_checkable
class _MarketContextEvidenceView(Protocol):
    """Structural view of Data-owned market-context evidence."""

    contract_version: str
    symbol: str
    spread: Decimal | None
    spread_unit: str | None
    liquidity: Decimal | None
    volatility: Decimal | None
    correlations: Mapping[str, Decimal]
    crisis_flags: tuple[str, ...]
    session_state: str | None
    calendar_state: str | None
    timezone: str
    provenance: Mapping[str, str]
    as_of: datetime
    expires_at: datetime
    request_id: str

    def model_dump(
        self,
        *,
        mode: str = "python",
        warnings: bool = True,
    ) -> dict[str, object]:
        """Return the complete market-context payload."""
        ...


def _utc(value: datetime) -> datetime:
    """Require an aware UTC timestamp.

    Args:
        value: Timestamp to validate.

    Returns:
        Validated timestamp.

    Raises:
        ValueError: If the timestamp is not aware UTC.
    """
    logger.debug("Validating Risk evidence UTC timestamp")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be aware UTC")
    return value


def _text(value: str) -> str:
    """Validate required trimmed text.

    Args:
        value: Text to validate.

    Returns:
        Validated text.

    Raises:
        ValueError: If text is empty or untrimmed.
    """
    logger.debug("Validating Risk evidence text")
    if not value or value != value.strip():
        raise ValueError("value must be non-empty trimmed text")
    return value


def _decimal_mapping(value: Mapping[str, Decimal]) -> Mapping[str, Decimal]:
    """Validate and freeze a finite Decimal mapping.

    Args:
        value: Mapping to validate.

    Returns:
        Immutable validated mapping.

    Raises:
        ValueError: If a key or Decimal is invalid.
    """
    logger.debug("Freezing Risk Decimal evidence mapping")
    validated: dict[str, Decimal] = {}
    for key, item in value.items():
        if not item.is_finite():
            raise ValueError("mapping values must be finite")
        validated[_text(key)] = item
    return MappingProxyType(validated)


def _text_mapping(value: Mapping[str, str]) -> Mapping[str, str]:
    """Validate and freeze a text mapping.

    Args:
        value: Mapping to validate.

    Returns:
        Immutable validated mapping.
    """
    logger.debug("Freezing Risk text evidence mapping")
    return MappingProxyType({_text(key): _text(item) for key, item in value.items()})


class _EvidenceModel(BaseModel):
    """Private strict immutable Risk evidence base."""

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        frozen=True,
        allow_inf_nan=False,
        arbitrary_types_allowed=True,
    )

    @field_validator(
        "request_id",
        "workflow_id",
        "correlation_id",
        check_fields=False,
    )
    @classmethod
    def _validate_trace_id(cls, value: str, info: ValidationInfo) -> str:
        """Validate a canonical prefixed UUID4 trace identifier.

        Args:
            value: Trace identifier to validate.
            info: Pydantic field metadata.

        Returns:
            Unchanged validated trace identifier.

        Raises:
            ValueError: If the identifier prefix or UUID4 syntax is invalid.
        """
        prefixes = {
            "request_id": "req",
            "workflow_id": "wf",
            "correlation_id": "cor",
        }
        prefix = prefixes.get(info.field_name or "")
        if prefix is None:
            raise ValueError("unsupported Risk trace identifier field")
        try:
            return validate_id(value, expected_prefix=prefix)
        except Exception as error:
            message = f"{info.field_name} must be a canonical prefixed UUID4"
            raise ValueError(message) from error


class PortfolioState(_EvidenceModel):
    """Normalized point-in-time account and portfolio evidence."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["risk.portfolio_state.v1"] = "risk.portfolio_state.v1"
    account_snapshot: _AccountStateSnapshotView
    peak_equity: Decimal
    day_start_equity: Decimal
    inception_equity: Decimal
    symbol_prices: Mapping[str, Decimal]
    symbol_contract_sizes: Mapping[str, Decimal]
    symbol_quote_currencies: Mapping[str, str]
    fx_conversions: tuple[_FXConversionEvidenceView, ...]
    return_timestamps: tuple[datetime, ...]
    return_history: Mapping[str, tuple[Decimal, ...]]
    correlations: Mapping[str, Decimal]
    exposure_dimensions: Mapping[str, tuple[str, ...]]
    as_of: datetime
    expires_at: datetime
    provenance: Mapping[str, str]
    missing_fields: tuple[str, ...]
    request_id: str
    workflow_id: str

    @field_validator("account_snapshot", mode="before")
    @classmethod
    def _validate_account_snapshot(cls, value: object) -> object:
        """Require an exact Data-owned account snapshot.

        Args:
            value: Candidate Data account snapshot.

        Returns:
            Exact validated Data account snapshot.

        Raises:
            TypeError: If the value does not implement Data's account contract.
            ValueError: If the value was not produced by Data's public API.
        """
        if not isinstance(value, _AccountStateSnapshotView):
            raise TypeError("account snapshot is incompatible")
        validated = build_account_state_snapshot(
            **value.model_dump(warnings=False, mode="python")
        )
        if type(value) is not type(validated):
            raise ValueError("account snapshot must be produced by Data")
        return validated

    @field_validator("fx_conversions", mode="before")
    @classmethod
    def _validate_fx_conversions(cls, value: object) -> object:
        """Require exact Data-owned FX conversion evidence.

        Args:
            value: Candidate conversion tuple.

        Returns:
            Exact validated conversion tuple.

        Raises:
            TypeError: If any value does not implement Data's FX contract.
            ValueError: If any value was not produced by Data's public API.
        """
        if not isinstance(value, tuple):
            raise TypeError("FX conversions must be a tuple")
        validated_items = []
        for item in value:
            if not isinstance(item, _FXConversionEvidenceView):
                raise TypeError("FX conversion evidence is incompatible")
            validated = build_fx_conversion_evidence(
                **item.model_dump(warnings=False, mode="python")
            )
            if type(item) is not type(validated):
                raise ValueError("FX conversion evidence must be produced by Data")
            validated_items.append(validated)
        return tuple(validated_items)

    @field_validator("request_id", "workflow_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate required identity text.

        Args:
            value: Text to validate.

        Returns:
            Validated text.
        """
        logger.debug("Validating PortfolioState identity")
        return _text(value)

    @field_validator("peak_equity", "day_start_equity", "inception_equity")
    @classmethod
    def _validate_decimal(cls, value: Decimal | None) -> Decimal | None:
        """Validate a finite monetary value.

        Args:
            value: Optional Decimal value.

        Returns:
            Validated value.

        Raises:
            ValueError: If the value is non-finite.
        """
        logger.debug("Validating PortfolioState monetary evidence")
        if value is not None and (not value.is_finite() or value < 0):
            raise ValueError("monetary values must be finite")
        return value

    @field_validator(
        "symbol_prices",
        "symbol_contract_sizes",
        "correlations",
        mode="after",
    )
    @classmethod
    def _freeze_decimals(cls, value: Mapping[str, Decimal]) -> Mapping[str, Decimal]:
        """Freeze a Decimal evidence mapping.

        Args:
            value: Mapping to freeze.

        Returns:
            Immutable mapping.
        """
        logger.debug("Freezing PortfolioState numeric evidence")
        return _decimal_mapping(value)

    @field_validator("provenance", mode="after")
    @classmethod
    def _freeze_provenance(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Freeze provenance evidence.

        Args:
            value: Provenance mapping.

        Returns:
            Immutable provenance.
        """
        logger.debug("Freezing PortfolioState provenance")
        return _text_mapping(value)

    @field_validator("symbol_quote_currencies", mode="after")
    @classmethod
    def _freeze_currencies(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze symbol quote currencies.

        Args:
            value: Symbol-to-currency mapping.

        Returns:
            Immutable validated mapping.

        Raises:
            ValueError: If a currency is not uppercase ISO-like text.
        """
        logger.debug("Freezing PortfolioState quote-currency evidence")
        checked = _text_mapping(value)
        if any(
            len(currency) != _CURRENCY_CODE_LENGTH or currency != currency.upper()
            for currency in checked.values()
        ):
            raise ValueError("quote currency must be three uppercase letters")
        return checked

    @field_validator("return_history", mode="after")
    @classmethod
    def _freeze_returns(
        cls, value: Mapping[str, tuple[Decimal, ...]]
    ) -> Mapping[str, tuple[Decimal, ...]]:
        """Validate and freeze aligned per-symbol returns.

        Args:
            value: Symbol return series.

        Returns:
            Immutable validated mapping.

        Raises:
            ValueError: If a return is non-finite.
        """
        logger.debug("Freezing PortfolioState return evidence")
        checked: dict[str, tuple[Decimal, ...]] = {}
        for symbol, returns in value.items():
            if any(not item.is_finite() for item in returns):
                raise ValueError("return evidence must be finite")
            checked[_text(symbol)] = returns
        return MappingProxyType(checked)

    @field_validator("exposure_dimensions", mode="after")
    @classmethod
    def _freeze_dimensions(
        cls, value: Mapping[str, tuple[str, ...]]
    ) -> Mapping[str, tuple[str, ...]]:
        """Validate and freeze symbol exposure dimensions.

        Args:
            value: Symbol-to-dimensions mapping.

        Returns:
            Immutable validated mapping.

        Raises:
            ValueError: If dimensions are empty or duplicated.
        """
        logger.debug("Freezing PortfolioState exposure dimensions")
        checked: dict[str, tuple[str, ...]] = {}
        for symbol, dimensions in value.items():
            items = tuple(_text(item) for item in dimensions)
            if not items or len(set(items)) != len(items):
                raise ValueError("exposure dimensions must be non-empty and unique")
            checked[_text(symbol)] = items
        return MappingProxyType(checked)

    @field_validator("as_of", "expires_at", "return_timestamps")
    @classmethod
    def _validate_time(
        cls, value: datetime | tuple[datetime, ...]
    ) -> datetime | tuple[datetime, ...]:
        """Validate a portfolio timestamp.

        Args:
            value: Timestamp or timestamps to validate.

        Returns:
            Validated timestamp.
        """
        logger.debug("Validating PortfolioState time")
        if isinstance(value, tuple):
            return tuple(_utc(item) for item in value)
        return _utc(value)

    @model_validator(mode="after")
    def _validate_state(self) -> PortfolioState:
        """Validate portfolio relationships.

        Returns:
            Validated state.

        Raises:
            ValueError: If state relationships are invalid.
        """
        logger.debug("Validating PortfolioState relationships")
        if self.expires_at <= self.as_of:
            raise ValueError("expires_at must follow as_of")
        self._validate_account_evidence()
        self._validate_symbol_evidence()
        self._validate_return_evidence()
        self._validate_fx_evidence()
        return self

    def _validate_account_evidence(self) -> None:
        """Validate Data account evidence and equity references.

        Raises:
            ValueError: If account evidence is stale or inconsistent.
        """
        logger.debug("Validating PortfolioState account evidence")
        if self.account_snapshot.contract_version != "v1":
            raise ValueError("account evidence version is incompatible")
        if (
            not self.account_snapshot.snapshot_at
            <= self.as_of
            <= self.account_snapshot.expires_at
        ):
            raise ValueError("account evidence is not current at state time")
        if self.expires_at > self.account_snapshot.expires_at:
            raise ValueError("state expiry exceeds account evidence expiry")
        if self.peak_equity < self.account_snapshot.equity:
            raise ValueError("peak equity cannot be below current equity")

    def _validate_symbol_evidence(self) -> None:
        """Validate complete valuation evidence for every referenced symbol.

        Raises:
            ValueError: If symbol valuation or correlation evidence is malformed.
        """
        logger.debug("Validating PortfolioState symbol valuation evidence")
        symbols = {
            *(item.symbol for item in self.account_snapshot.positions),
            *(item.symbol for item in self.account_snapshot.orders),
            *self.return_history.keys(),
        }
        for pair, correlation in self.correlations.items():
            parts = pair.split("|")
            if len(parts) != _CORRELATION_PAIR_SIZE or parts[0] >= parts[1]:
                raise ValueError("correlation key must be a canonical lexical pair")
            if not Decimal(-1) <= correlation <= Decimal(1):
                raise ValueError("correlation must be between -1 and 1")
            symbols.update(parts)
        required_mappings = (
            self.symbol_prices,
            self.symbol_contract_sizes,
            self.symbol_quote_currencies,
            self.exposure_dimensions,
        )
        if any(not symbols.issubset(mapping.keys()) for mapping in required_mappings):
            raise ValueError("referenced symbol lacks complete valuation metadata")
        if any(self.symbol_prices[symbol] <= 0 for symbol in symbols):
            raise ValueError("symbol price must be positive")
        if any(self.symbol_contract_sizes[symbol] <= 0 for symbol in symbols):
            raise ValueError("symbol contract size must be positive")

    def _validate_return_evidence(self) -> None:
        """Validate exact timestamp alignment for supplied return series.

        Raises:
            ValueError: If timestamps or series lengths are unaligned.
        """
        logger.debug("Validating PortfolioState aligned return evidence")
        if tuple(sorted(self.return_timestamps)) != self.return_timestamps or len(
            set(self.return_timestamps)
        ) != len(self.return_timestamps):
            raise ValueError("return timestamps must be strictly increasing")
        expected = len(self.return_timestamps)
        if any(len(series) != expected for series in self.return_history.values()):
            raise ValueError("return histories are not timestamp aligned")
        if bool(self.return_history) != bool(self.return_timestamps):
            raise ValueError(
                "return timestamps and histories must be supplied together"
            )

    def _validate_fx_evidence(self) -> None:
        """Validate unique current quote-to-base conversion evidence.

        Raises:
            ValueError: If a required conversion is absent, stale, or ambiguous.
        """
        logger.debug("Validating PortfolioState FX conversion evidence")
        base_currency = self.account_snapshot.currency
        conversions: dict[str, _FXConversionEvidenceView] = {}
        for evidence in self.fx_conversions:
            if (
                evidence.contract_version != "v1"
                or evidence.target_currency != base_currency
            ):
                raise ValueError("FX conversion evidence is incompatible")
            if evidence.source_currency in conversions:
                raise ValueError("FX conversion evidence is ambiguous")
            if not evidence.as_of <= self.as_of <= evidence.expires_at:
                raise ValueError("FX conversion evidence is stale")
            if self.expires_at > evidence.expires_at:
                raise ValueError("state expiry exceeds FX evidence expiry")
            conversions[evidence.source_currency] = evidence
        required = {
            currency
            for currency in self.symbol_quote_currencies.values()
            if currency != base_currency
        }
        if not required.issubset(conversions):
            raise ValueError("required quote-to-base FX evidence is missing")

    @field_serializer("symbol_prices", "symbol_contract_sizes", "correlations")
    def _serialize_decimals(self, value: Mapping[str, Decimal]) -> dict[str, str]:
        """Serialize an exact Decimal mapping.

        Args:
            value: Decimal mapping.

        Returns:
            Exact string mapping.
        """
        logger.debug("Serializing PortfolioState Decimal mapping")
        return {key: str(item) for key, item in value.items()}

    @field_serializer("provenance")
    def _serialize_provenance(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize provenance.

        Args:
            value: Provenance mapping.

        Returns:
            Ordinary mapping.
        """
        logger.debug("Serializing PortfolioState provenance")
        return dict(value)

    @field_serializer(
        "symbol_quote_currencies", "return_history", "exposure_dimensions"
    )
    def _serialize_nested_mapping(
        self, value: Mapping[str, object]
    ) -> dict[str, object]:
        """Serialize an immutable nested evidence mapping.

        Args:
            value: Immutable evidence mapping.

        Returns:
            Ordinary mapping.
        """
        logger.debug("Serializing PortfolioState nested evidence mapping")
        return dict(value)


class PortfolioRiskSnapshot(_EvidenceModel):
    """Reproducible immutable portfolio risk measurements."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["risk.portfolio_risk_snapshot.v1"] = (
        "risk.portfolio_risk_snapshot.v1"
    )
    snapshot_id: str
    account_id: str
    base_currency: str
    equity: Decimal
    initial_balance: Decimal | None = None
    daily_loss: Decimal
    total_loss: Decimal
    current_day_profit: Decimal | None = None
    cumulative_profit: Decimal | None = None
    proposal_best_case_profit: Decimal | None = None
    gross_exposure: Decimal
    net_exposure: Decimal
    drawdown: Decimal
    peak_equity: Decimal | None = None
    highest_eod_balance: Decimal | None = None
    margin_utilization: Decimal | None
    effective_leverage: Decimal | None
    historical_var: Decimal | None
    historical_cvar: Decimal | None
    volatility: Decimal | None
    portfolio_correlation: Decimal | None
    exposure_by_dimension: Mapping[str, Decimal]
    contributions: Mapping[str, Decimal]
    limit_statuses: Mapping[str, LimitStatus]
    assumptions: tuple[str, ...]
    coverage: Mapping[str, str]
    gaps: tuple[str, ...]
    regime: str | None
    as_of: datetime
    config_hash: str
    evidence_refs: Mapping[str, str]
    request_id: str
    workflow_id: str

    @field_validator(
        "snapshot_id",
        "account_id",
        "base_currency",
        "config_hash",
        "request_id",
        "workflow_id",
    )
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate snapshot identity text.

        Args:
            value: Text to validate.

        Returns:
            Validated text.
        """
        logger.debug("Validating PortfolioRiskSnapshot identity")
        return _text(value)

    @field_validator("as_of")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate snapshot time.

        Args:
            value: Timestamp to validate.

        Returns:
            Validated timestamp.
        """
        logger.debug("Validating PortfolioRiskSnapshot time")
        return _utc(value)

    @field_validator(
        "equity",
        "initial_balance",
        "daily_loss",
        "total_loss",
        "current_day_profit",
        "cumulative_profit",
        "proposal_best_case_profit",
        "gross_exposure",
        "net_exposure",
        "drawdown",
        "peak_equity",
        "highest_eod_balance",
        "margin_utilization",
        "effective_leverage",
        "historical_var",
        "historical_cvar",
        "volatility",
        "portfolio_correlation",
    )
    @classmethod
    def _validate_metric(cls, value: Decimal | None) -> Decimal | None:
        """Validate a finite snapshot metric.

        Args:
            value: Optional metric.

        Returns:
            Validated metric.

        Raises:
            ValueError: If the metric is non-finite.
        """
        logger.debug("Validating PortfolioRiskSnapshot metric")
        if value is not None and not value.is_finite():
            raise ValueError("snapshot metric must be finite")
        return value

    @field_validator("exposure_by_dimension", "contributions", mode="after")
    @classmethod
    def _freeze_decimals(cls, value: Mapping[str, Decimal]) -> Mapping[str, Decimal]:
        """Freeze snapshot Decimal mappings.

        Args:
            value: Mapping to freeze.

        Returns:
            Immutable mapping.
        """
        logger.debug("Freezing PortfolioRiskSnapshot Decimal mapping")
        return _decimal_mapping(value)

    @field_validator("coverage", "evidence_refs", mode="after")
    @classmethod
    def _freeze_texts(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Freeze snapshot text mappings.

        Args:
            value: Mapping to freeze.

        Returns:
            Immutable mapping.
        """
        logger.debug("Freezing PortfolioRiskSnapshot text mapping")
        return _text_mapping(value)

    @field_validator("limit_statuses", mode="after")
    @classmethod
    def _freeze_statuses(
        cls, value: Mapping[str, LimitStatus]
    ) -> Mapping[str, LimitStatus]:
        """Freeze snapshot limit statuses.

        Args:
            value: Limit-status mapping.

        Returns:
            Immutable mapping.
        """
        logger.debug("Freezing PortfolioRiskSnapshot limit statuses")
        return MappingProxyType({_text(key): item for key, item in value.items()})

    @field_serializer("exposure_by_dimension", "contributions")
    def _serialize_decimals(self, value: Mapping[str, Decimal]) -> dict[str, str]:
        """Serialize snapshot Decimal mapping.

        Args:
            value: Decimal mapping.

        Returns:
            Exact string mapping.
        """
        logger.debug("Serializing PortfolioRiskSnapshot Decimal mapping")
        return {key: str(item) for key, item in value.items()}

    @field_serializer("coverage", "evidence_refs", "limit_statuses")
    def _serialize_mapping(self, value: Mapping[str, object]) -> dict[str, object]:
        """Serialize snapshot mapping.

        Args:
            value: Immutable mapping.

        Returns:
            Ordinary mapping.
        """
        logger.debug("Serializing PortfolioRiskSnapshot mapping")
        return dict(value)


@guard_risk_boundary(risk_level="medium", read_only=True)
def validate_market_context_evidence(
    evidence: _MarketContextEvidenceView, *, now: datetime
) -> None:
    """Validate Data-owned market context for Risk use.

    Args:
        evidence: Data-owned evidence to validate.
        now: Injected current UTC time.

    Raises:
        RiskDomainError: If evidence is incompatible, stale, or malformed.
    """
    logger.info("Validating Data-owned market-context evidence for Risk")
    if not isinstance(evidence, _MarketContextEvidenceView):
        raise RiskDomainError(
            RiskErrorCode.VALIDATION_FAILED,
            "market-context evidence is incompatible",
        )
    payload = evidence.model_dump(warnings=False, mode="python")
    payload["correlations"] = dict(evidence.correlations)
    payload["provenance"] = dict(evidence.provenance)
    validated = build_market_context_evidence(**payload)
    if type(evidence) is not type(validated):
        raise RiskDomainError(
            RiskErrorCode.VALIDATION_FAILED,
            "market-context evidence must be produced by Data",
        )
    try:
        checked_now = _utc(now)
    except ValueError as error:
        raise RiskDomainError(RiskErrorCode.VALIDATION_FAILED, str(error)) from error
    if evidence.contract_version != "v1":
        raise RiskDomainError(RiskErrorCode.VALIDATION_FAILED, "incompatible evidence")
    if not evidence.provenance:
        raise RiskDomainError(RiskErrorCode.MISSING_EVIDENCE, "missing provenance")
    if checked_now > evidence.expires_at:
        raise RiskDomainError(RiskErrorCode.STALE_EVIDENCE, "expired evidence")


__all__ = [
    "PortfolioRiskSnapshot",
    "PortfolioState",
    "validate_market_context_evidence",
]
