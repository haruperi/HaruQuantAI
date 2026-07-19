"""Immutable Simulation result, trade-ledger, and artifact contracts."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import PurePosixPath
from typing import Literal, override

from pydantic import (
    BaseModel,
    ConfigDict,
    field_validator,
    model_validator,
)

from app.services.trading import ExecutionReceipt  # noqa: TC001
from app.utils import logger

CANONICAL_ARTIFACT_TYPES = ("journal.jsonl", "result.json", "report.md")
REPORT_SCHEMA_VERSION = "v1"
_HASH_LENGTH = 64
_MINIMUM_COMMON_RETURN_OBSERVATIONS = 30


class _Contract(BaseModel):
    """Private strict immutable reporting-contract behavior."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    @override
    def model_post_init(self, context: object) -> None:
        """Log immutable reporting-contract construction.

        Args:
            context: Optional Pydantic construction context.
        """
        logger.debug(
            "Constructed Simulation reporting contract %s", type(self).__name__
        )
        del context


def _validate_utc(value: datetime) -> datetime:
    """Validate one aware UTC timestamp.

    Args:
        value: Candidate timestamp.

    Returns:
        Validated timestamp.

    Raises:
        ValueError: If time is not UTC.
    """
    logger.debug("Validating Simulation reporting timestamp")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("Reporting timestamps must be aware UTC")
    return value


def _validate_hash(value: str) -> str:
    """Validate one lowercase SHA-256 digest.

    Args:
        value: Candidate digest.

    Returns:
        Validated digest.

    Raises:
        ValueError: If malformed.
    """
    logger.debug("Validating Simulation reporting hash")
    if len(value) != _HASH_LENGTH or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError("Reporting hash must be lowercase SHA-256 hex")
    return value


class ArtifactEntry(_Contract):
    """Versioned identity for one completed canonical artifact."""

    relative_path: str
    media_type: str
    size_bytes: int
    sha256: str
    schema_version: Literal["v1"] = "v1"
    created_at: datetime

    @field_validator("relative_path")
    @classmethod
    def _validate_path(cls, value: str) -> str:
        """Validate a safe canonical relative artifact path.

        Args:
            value: Candidate relative path.

        Returns:
            Validated path.

        Raises:
            ValueError: If absolute, nested, or unsafe.
        """
        logger.debug("Validating canonical Simulation artifact path")
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts or len(path.parts) != 1:
            raise ValueError("Artifact path must be one safe relative name")
        if value not in CANONICAL_ARTIFACT_TYPES:
            raise ValueError("Artifact path is not canonical")
        return value

    @field_validator("sha256")
    @classmethod
    def _validate_digest(cls, value: str) -> str:
        """Validate artifact checksum.

        Args:
            value: Candidate checksum.

        Returns:
            Validated checksum.
        """
        logger.debug("Validating Simulation artifact checksum")
        return _validate_hash(value)

    @field_validator("created_at")
    @classmethod
    def _validate_created_at(cls, value: datetime) -> datetime:
        """Validate artifact creation time.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.
        """
        logger.debug("Validating Simulation artifact creation time")
        return _validate_utc(value)

    @field_validator("size_bytes")
    @classmethod
    def _validate_size(cls, value: int) -> int:
        """Validate positive artifact size.

        Args:
            value: Candidate byte count.

        Returns:
            Validated size.

        Raises:
            ValueError: If not positive.
        """
        logger.debug("Validating Simulation artifact size")
        if value <= 0:
            raise ValueError("Canonical artifact must be non-empty")
        return value


class ArtifactManifest(_Contract):
    """Acyclic manifest covering every canonical evidence artifact."""

    artifacts: tuple[ArtifactEntry, ...]
    created_at: datetime
    schema_version: Literal["v1"] = "v1"

    @field_validator("created_at")
    @classmethod
    def _validate_created_at(cls, value: datetime) -> datetime:
        """Validate manifest creation time.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.
        """
        logger.debug("Validating Simulation manifest creation time")
        return _validate_utc(value)

    @model_validator(mode="after")
    def _validate_manifest(self) -> ArtifactManifest:
        """Require one ordered entry for every canonical artifact.

        Returns:
            Validated manifest.

        Raises:
            ValueError: If entries are missing, duplicated, or unordered.
        """
        logger.debug("Validating complete Simulation artifact manifest")
        paths = tuple(entry.relative_path for entry in self.artifacts)
        if paths != CANONICAL_ARTIFACT_TYPES:
            raise ValueError("Manifest must contain canonical artifacts in order")
        return self


class ClosedTradeRecord(_Contract):
    """Exact Analytics-compatible seventeen-field closed-trade record."""

    ticket: str
    symbol: str
    type: Literal["BUY", "SELL"]
    volume: Decimal
    entry_time: datetime
    entry_price: Decimal
    stop_loss: Decimal | None
    take_profit: Decimal | None
    exit_time: datetime
    exit_price: Decimal
    comment: str
    commission: Decimal
    swap: Decimal
    profit: Decimal
    magic: str
    mae: Decimal | None
    mfe: Decimal | None

    @field_validator(
        "volume",
        "entry_price",
        "stop_loss",
        "take_profit",
        "exit_price",
        "commission",
        "swap",
        "profit",
        "mae",
        "mfe",
    )
    @classmethod
    def _validate_decimal(cls, value: Decimal | None, info: object) -> Decimal | None:
        """Validate exact closed-trade numeric evidence.

        Args:
            value: Candidate Decimal.
            info: Pydantic field information.

        Returns:
            Validated value.

        Raises:
            ValueError: If finite or sign requirements fail.
        """
        logger.debug("Validating Simulation closed-trade Decimal")
        if value is None:
            return None
        if not value.is_finite():
            raise ValueError("Closed-trade values must be finite")
        field = str(getattr(info, "field_name", ""))
        if (
            field in {"volume", "entry_price", "exit_price", "stop_loss", "take_profit"}
            and value <= 0
        ):
            raise ValueError("Closed-trade volume and prices must be positive")
        if field in {"commission", "swap", "mae"} and value > 0:
            raise ValueError("Closed-trade costs and MAE must be non-positive")
        if field == "mfe" and value < 0:
            raise ValueError("Closed-trade MFE must be non-negative")
        return value

    @field_validator("entry_time", "exit_time")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate closed-trade UTC time.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated timestamp.
        """
        logger.debug("Validating Simulation closed-trade time")
        return _validate_utc(value)

    @model_validator(mode="after")
    def _validate_window(self) -> ClosedTradeRecord:
        """Validate the closed-trade measurement window.

        Returns:
            Validated record.

        Raises:
            ValueError: If exit precedes entry.
        """
        logger.debug("Validating Simulation closed-trade window")
        if self.exit_time < self.entry_time:
            raise ValueError("Closed-trade exit cannot precede entry")
        return self


class AccountingSummary(_Contract):
    """Exact completed-run accounting totals."""

    final_balance: Decimal
    final_equity: Decimal
    used_margin: Decimal
    free_margin: Decimal
    gross_profit: Decimal
    commission: Decimal
    swap: Decimal
    net_profit: Decimal


class RealismDisclosure(_Contract):
    """Explicit execution and data realism disclosure."""

    tick_model: str
    slippage_model: str
    liquidity_model: str
    session_model: str
    data_quality: str
    assumptions: tuple[str, ...]
    limitations: tuple[str, ...]


class SimulationResult(_Contract):
    """Completed deterministic canonical Simulation result version 1."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["simulation.result.v1"] = "simulation.result.v1"
    run_id: str
    request_hash: str
    config_hash: str
    data_hash: str
    engine_version: str
    status: Literal["completed"]
    journal_ref: str
    artifact_manifest_ref: str
    fills: tuple[ExecutionReceipt, ...]
    closed_trades: tuple[ClosedTradeRecord, ...]
    initial_balance: Decimal
    account_currency: str
    accounting: AccountingSummary
    diagnostics: tuple[str, ...]
    realism: RealismDisclosure

    @field_validator("request_hash", "config_hash", "data_hash")
    @classmethod
    def _validate_identity_hash(cls, value: str) -> str:
        """Validate result reproducibility hash.

        Args:
            value: Candidate digest.

        Returns:
            Validated digest.
        """
        logger.debug("Validating Simulation result identity hash")
        return _validate_hash(value)

    @field_validator("initial_balance")
    @classmethod
    def _validate_balance(cls, value: Decimal) -> Decimal:
        """Validate positive finite initial balance.

        Args:
            value: Candidate balance.

        Returns:
            Validated balance.

        Raises:
            ValueError: If invalid.
        """
        logger.debug("Validating Simulation initial balance")
        if not value.is_finite() or value <= 0:
            raise ValueError("Initial balance must be finite and positive")
        return value


class PortfolioComponentResult(_Contract):
    """One exact reconciled portfolio component result row."""

    component_id: str
    simulation_result_id: str
    journal_ref: str
    metrics_ref: str
    account_currency: str
    reconciled: Literal[True]


class ReturnObservation(_Contract):
    """One UTC component return observation."""

    timestamp: datetime
    return_value: Decimal

    @field_validator("timestamp")
    @classmethod
    def _validate_timestamp(cls, value: datetime) -> datetime:
        """Validate return observation time.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated timestamp.
        """
        logger.debug("Validating Simulation component-return time")
        return _validate_utc(value)


class ComponentReturnSeries(_Contract):
    """Ordered return evidence for one simulated component."""

    component_id: str
    simulation_result_id: str
    observations: tuple[ReturnObservation, ...]


class RiskBudgetHistoryRow(_Contract):
    """Preserved Risk-owned component budget evidence."""

    risk_decision_id: str
    component_id: str
    effective_at: datetime
    expires_at: datetime
    approved_budget: Decimal
    currency: str


class PortfolioSimulationResult(_Contract):
    """Completed reconciled portfolio-level Simulation result version 1."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["simulation.portfolio_result.v1"] = (
        "simulation.portfolio_result.v1"
    )
    result_id: str
    run_id: str
    request_hash: str
    config_hash: str
    data_hash: str
    result_hash: str
    engine_version: str
    status: Literal["completed"]
    portfolio_id: str
    construction_result_id: str
    construction_version: str
    measurement_start: datetime
    measurement_end: datetime
    base_currency: str
    component_results: tuple[PortfolioComponentResult, ...]
    component_return_series: tuple[ComponentReturnSeries, ...]
    aggregate_journal_ref: str
    aggregate_metrics_ref: str
    risk_budget_history: tuple[RiskBudgetHistoryRow, ...]
    fx_evidence_ids: tuple[str, ...]
    artifact_manifest_ref: str

    @model_validator(mode="after")
    def _validate_portfolio(self) -> PortfolioSimulationResult:
        """Validate portfolio reconciliation and aligned return evidence.

        Returns:
            Validated portfolio result.

        Raises:
            ValueError: If component or return evidence is incomplete.
        """
        logger.debug("Validating complete Simulation portfolio result")
        if self.measurement_end < self.measurement_start:
            raise ValueError("Portfolio measurement window is invalid")
        component_pairs = {
            (row.component_id, row.simulation_result_id)
            for row in self.component_results
        }
        return_pairs = {
            (row.component_id, row.simulation_result_id)
            for row in self.component_return_series
        }
        if not component_pairs or component_pairs != return_pairs:
            raise ValueError(
                "Every portfolio component requires matching return evidence"
            )
        timestamp_sets: list[set[datetime]] = []
        for series in self.component_return_series:
            timestamps = tuple(item.timestamp for item in series.observations)
            if timestamps != tuple(sorted(timestamps)) or len(timestamps) != len(
                set(timestamps)
            ):
                raise ValueError(
                    "Component return timestamps must be unique and ordered"
                )
            if any(
                timestamp < self.measurement_start or timestamp > self.measurement_end
                for timestamp in timestamps
            ):
                raise ValueError(
                    "Component return timestamp is outside measurement window"
                )
            timestamp_sets.append(set(timestamps))
        common = set.intersection(*timestamp_sets)
        if len(common) < _MINIMUM_COMMON_RETURN_OBSERVATIONS:
            raise ValueError(
                "Portfolio components require 30 common return observations"
            )
        return self


class FastResearchResult(_Contract):
    """Explicit non-canonical approximate research result."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["simulation.fast_research_result.v1"] = (
        "simulation.fast_research_result.v1"
    )
    request_hash: str
    config_hash: str
    data_hash: str
    canonical: Literal[False] = False
    observations: tuple[Decimal, ...]
    assumptions: tuple[str, ...]
    limitations: tuple[str, ...]
    generated_at: datetime


__all__ = [
    "CANONICAL_ARTIFACT_TYPES",
    "REPORT_SCHEMA_VERSION",
    "AccountingSummary",
    "ArtifactEntry",
    "ArtifactManifest",
    "ClosedTradeRecord",
    "ComponentReturnSeries",
    "FastResearchResult",
    "PortfolioComponentResult",
    "PortfolioSimulationResult",
    "RealismDisclosure",
    "ReturnObservation",
    "RiskBudgetHistoryRow",
    "SimulationResult",
]
