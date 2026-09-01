"""Fail-closed request, scope, and market-data validation."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Literal

from app.composition.logging import get_logger
from app.kernel.serialization import canonical_digest, canonical_json
from app.services.data import is_ohlcv_record, is_tick_record
from app.services.simulator.errors import SimulationError
from app.services.simulator.validation.contracts import (
    MarketDataValidationContext,
    MarketEvidenceLineage,
    ValidatedMarketDataEvidence,
)

MarketDataset = Any
OHLCVRecord = Any
TickRecord = Any

logger = get_logger(__name__)

SUPPORTED_ASSET_CLASSES = ("FX",)
_REQUIRED_INPUT_FIELDS = (
    "request_id",
    "workflow_id",
    "correlation_id",
    "strategy_id",
    "strategy_version",
    "strategy_config_ref",
    "strategy_config_hash",
    "data_ref",
    "data_version",
    "data_hash",
    "execution_profile_ref",
    "execution_profile_version",
    "execution_profile_hash",
    "risk_policy_ref",
    "risk_policy_version",
    "risk_policy_hash",
    "symbol",
    "config_hash",
)
_UNSAFE_KEYS = {"code", "source_code", "module_path", "file_path", "callable"}


def _raise(
    code: str, message: str, payload: Mapping[str, object] | None = None
) -> None:
    """Raise one controlled validation error.

    Args:
        code: Cataloged error code.
        message: Safe explanation.
        payload: Optional payload supplying request identity.

    Raises:
        SimulationError: Always.
    """
    logger.debug("Raising Simulation validation error %s", code)
    request_id = None if payload is None else payload.get("request_id")
    raise SimulationError(
        code,
        message,
        request_id=request_id if isinstance(request_id, str) else None,
    )


def _dataset_hash(dataset: MarketDataset) -> str:
    """Calculate the canonical identity of a market dataset.

    Args:
        dataset: Dataset to identify.

    Returns:
        Lowercase SHA-256 digest.
    """
    logger.debug("Hashing one Data MarketDataset for Simulation")
    material = dataset.model_dump(mode="python", warnings=False)
    return canonical_digest(material)


def validate_run_inputs(payload: Mapping[str, object]) -> None:
    """Validate reference-based run material before domain execution.

    Args:
        payload: Canonical request projection.

    Raises:
        SimulationError: If required or safe material cannot be proven.
    """
    logger.info("Validating Simulation run input references")
    if any(key.casefold() in _UNSAFE_KEYS for key in payload):
        _raise(
            "SIM_ARBITRARY_CODE_REJECTED",
            "Raw code or path input is prohibited",
            payload,
        )
    symbol = payload.get("symbol")
    if not isinstance(symbol, str) or not symbol.strip():
        _raise("SIM_MISSING_SYMBOL", "A non-empty symbol is required", payload)
    start = payload.get("start")
    end = payload.get("end")
    if isinstance(start, datetime) and isinstance(end, datetime) and end < start:
        _raise("SIM_INVALID_DATE_RANGE", "Run date range is invalid", payload)
    missing = tuple(field for field in _REQUIRED_INPUT_FIELDS if not payload.get(field))
    if missing:
        _raise("SIM_INVALID_CONFIG", "Required run identity is missing", payload)
    try:
        canonical_json(payload)
    except ValueError as error:
        logger.warning(
            "Simulation input serialization was rejected: %s", type(error).__name__
        )
        _raise(
            "SIM_INVALID_CONFIG", "Run input is not deterministic JSON-safe", payload
        )


def validate_phase_one_scope(payload: Mapping[str, object]) -> None:
    """Enforce the approved Phase 1 asset, profile, and route boundary.

    Args:
        payload: Request scope projection.

    Raises:
        SimulationError: If the requested scope is unsupported.
    """
    logger.info("Validating Simulation Phase 1 scope")
    if payload.get("asset_class") not in SUPPORTED_ASSET_CLASSES:
        _raise(
            "SIM_UNSUPPORTED_ASSET_CLASS", "Only FX is supported in Phase 1", payload
        )
    profile = payload.get("runtime_profile")
    if profile not in {"simulation", "fast_research"}:
        _raise("SIM_UNSUPPORTED_OPERATION", "Runtime profile is unsupported", payload)
    if payload.get("execution_route") != "sim":
        _raise("SIM_UNSUPPORTED_OPERATION", "Only the sim route is supported", payload)
    if profile == "fast_research" and payload.get("canonical") is True:
        _raise(
            "SIM_UNSUPPORTED_FEATURE",
            "Fast research cannot claim canonical status",
            payload,
        )


def _validate_records(dataset: MarketDataset) -> None:
    """Validate record ordering and price invariants.

    Args:
        dataset: Dataset whose records are checked.

    Raises:
        SimulationError: If record evidence is invalid.
    """
    logger.debug("Validating Simulation market-data records")
    if dataset.record_count != len(dataset.records) or not dataset.records:
        _raise(
            "SIM_DATA_COVERAGE_INSUFFICIENT", "Dataset record coverage is incomplete"
        )
    timestamps = tuple(record.timestamp for record in dataset.records)
    if timestamps != tuple(sorted(timestamps)):
        _raise("SIM_DATA_NON_MONOTONIC", "Dataset timestamps are not monotonic")
    if len(set(timestamps)) != len(timestamps):
        _raise("SIM_DATA_DUPLICATE_TIMESTAMP", "Dataset timestamps are not unique")
    for record in dataset.records:
        if any(
            value.tzinfo is None or value.utcoffset() != timedelta(0)
            for value in (record.timestamp, record.available_at)
        ):
            _raise("SIM_DATA_SCHEMA_INVALID", "Record timestamps must be aware UTC")
        numeric = tuple(
            getattr(record, field, None)
            for field in (
                "open",
                "high",
                "low",
                "close",
                "bid",
                "ask",
                "last",
                "volume",
            )
        )
        if any(
            value is not None
            and (not isinstance(value, Decimal) or not value.is_finite())
            for value in numeric
        ):
            _raise("SIM_DATA_SCHEMA_INVALID", "Record numerics must be finite Decimal")
        if is_ohlcv_record(record) and not (
            record.low <= record.open <= record.high
            and record.low <= record.close <= record.high
        ):
            _raise("SIM_DATA_OHLC_INVALID", "OHLC relationships are invalid")
        if is_tick_record(record) and (
            record.bid is not None
            and record.ask is not None
            and record.ask < record.bid
        ):
            _raise("SIM_DATA_SPREAD_NEGATIVE", "Tick spread is negative")


def validate_market_data(
    dataset: MarketDataset,
    context: MarketDataValidationContext,
) -> ValidatedMarketDataEvidence:
    """Validate one Data-owned dataset against explicit run evidence.

    Args:
        dataset: Data-owned immutable dataset.
        context: Exact hash, coverage, time, and model expectations.

    Returns:
        Immutable validation evidence.

    Raises:
        SimulationError: If any execution-critical evidence fails.
    """
    logger.info("Validating market data for Simulation request %s", dataset.request_id)
    actual_hash = _dataset_hash(dataset)
    if actual_hash != context.expected_data_hash:
        _raise("SIM_DATA_CHECKSUM_MISMATCH", "Market dataset checksum does not match")
    if dataset.start > context.requested_start or dataset.end < context.requested_end:
        _raise(
            "SIM_DATA_COVERAGE_INSUFFICIENT", "Market dataset coverage is insufficient"
        )
    if dataset.available_at > context.evaluated_at:
        _raise("SIM_LOOKAHEAD_DETECTED", "Market dataset is not yet available")
    if context.evaluated_at - dataset.available_at > context.maximum_staleness:
        _raise("SIM_DATA_STALE", "Market dataset is stale")
    if dataset.quality_report.quality_decision in {"rejected", "not_evaluated"}:
        _raise("SIM_DATA_SCHEMA_INVALID", "Market dataset quality is not approved")
    _validate_records(dataset)
    tick_model = dataset.source_metadata.get("tick_generation_model", "")
    if dataset.data_kind != "ticks" or tick_model not in context.allowed_tick_models:
        _raise("SIM_UNSUPPORTED_TICK_MODEL", "Dataset is not an approved tick series")
    return ValidatedMarketDataEvidence(
        data_hash=actual_hash,
        dataset_schema_id=dataset.schema_id,
        tick_model=tick_model,
        record_count=dataset.record_count,
        validated_at=context.evaluated_at,
    )


def validate_market_evidence_lineage(  # noqa: C901, PLR0912
    source_dataset: MarketDataset,
    tick_dataset: MarketDataset,
    *,
    decision_instant: datetime,
    runtime_profile: str,
    path_sensitive: bool,
    required_clock_edges: tuple[str, ...],
    clock_edges: Mapping[str, datetime | None],
) -> MarketEvidenceLineage:
    """Validate source/tick lineage and point-in-time parity eligibility.

    Args:
        source_dataset: Data-owned source bars or genuine tick dataset.
        tick_dataset: Data-owned tick evidence after any derivation.
        decision_instant: Exact simulated decision timestamp.
        runtime_profile: ``simulation`` or ``fast_research``.
        path_sensitive: Whether the requested behavior depends on intrabar order.
        required_clock_edges: Predeclared clock edges required by the envelope.
        clock_edges: Evidenced edge timestamps; absence remains explicit.

    Returns:
        Immutable independent hashes, classification, coverage, and eligibility.

    Raises:
        SimulationError: If lineage, availability, classification, or timing fails.
    """
    if decision_instant.tzinfo is None or decision_instant.utcoffset() != timedelta(0):
        _raise("SIM_INVALID_CONFIG", "Decision instant must be aware UTC")
    if runtime_profile not in {"simulation", "fast_research"}:
        _raise("SIM_UNSUPPORTED_OPERATION", "Runtime profile is unsupported")
    if not source_dataset.records or not tick_dataset.records:
        _raise("SIM_DATA_COVERAGE_INSUFFICIENT", "Lineage datasets cannot be empty")
    _validate_records(source_dataset)
    _validate_records(tick_dataset)
    for dataset in (source_dataset, tick_dataset):
        if dataset.available_at > decision_instant or any(
            record.available_at > decision_instant for record in dataset.records
        ):
            _raise("SIM_LOOKAHEAD_DETECTED", "Market evidence is not yet available")

    model = str(tick_dataset.source_metadata.get("tick_generation_model", ""))
    declared_class = tick_dataset.source_metadata.get("market_evidence_class")
    evidence_class: Literal[
        "genuine_bid_ask_ticks", "depth_supported_ticks", "derived_bar_model"
    ]
    if declared_class == "depth_supported_ticks":
        evidence_class = "depth_supported_ticks"
    elif model == "real":
        evidence_class = "genuine_bid_ask_ticks"
    elif model:
        evidence_class = "derived_bar_model"
    else:
        _raise("SIM_UNSUPPORTED_TICK_MODEL", "Tick lineage model is missing")
    if any(
        not is_tick_record(record) or record.bid is None or record.ask is None
        for record in tick_dataset.records
    ):
        _raise("SIM_SPREAD_MISSING", "Tick lineage requires bid and ask evidence")
    if path_sensitive and evidence_class == "derived_bar_model":
        _raise(
            "SIM_UNSUPPORTED_TICK_MODEL",
            "Derived-bar evidence is not pathwise parity eligible",
        )
    if evidence_class == "derived_bar_model" and runtime_profile != "fast_research":
        _raise(
            "SIM_UNSUPPORTED_TICK_MODEL",
            "Derived-bar evidence requires fast research or a registered invariant",
        )

    if required_clock_edges != tuple(sorted(set(required_clock_edges))):
        _raise("SIM_INVALID_CONFIG", "Required clock edges must be ordered and unique")
    evidenced: list[str] = []
    for name, value in sorted(clock_edges.items()):
        if value is None:
            continue
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            _raise("SIM_INVALID_CONFIG", "Clock-edge timestamps must be aware UTC")
        evidenced.append(name)
    missing = tuple(edge for edge in required_clock_edges if edge not in evidenced)
    return MarketEvidenceLineage(
        source_lineage_hash=_dataset_hash(source_dataset),
        tick_lineage_hash=_dataset_hash(tick_dataset),
        market_evidence_class=evidence_class,
        tick_model=model,
        decision_instant=decision_instant,
        evidenced_clock_edges=tuple(evidenced),
        missing_clock_edges=missing,
        parity_eligible=not missing,
    )


__all__ = [
    "SUPPORTED_ASSET_CLASSES",
    "validate_market_data",
    "validate_market_evidence_lineage",
    "validate_phase_one_scope",
    "validate_run_inputs",
]
