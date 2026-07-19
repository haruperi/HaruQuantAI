"""Complete portfolio-allocation evidence projection for Analytics."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.services.analytics.contracts.evidence import to_report_json_safe
from app.services.analytics.contracts.models import (
    AnalyticsRunConfig,
    MetricEvidence,
    PerformanceReport,
    PortfolioAllocationEvidence,
    PortfolioRebalanceMeasurementEvidence,
    PortfolioRebalanceMeasurementRequest,
    SectionEvidence,
)
from app.services.analytics.reports.portfolio import (
    _fx_rate,
    _measurement_window,
    build_portfolio_performance_report,
)
from app.utils import canonical_json, logger

_PORTFOLIO_RESULT_FIELDS = frozenset(
    {
        "contract_version",
        "schema_id",
        "result_id",
        "run_id",
        "request_hash",
        "config_hash",
        "data_hash",
        "result_hash",
        "engine_version",
        "status",
        "portfolio_id",
        "construction_result_id",
        "construction_version",
        "measurement_start",
        "measurement_end",
        "base_currency",
        "component_results",
        "component_return_series",
        "aggregate_journal_ref",
        "aggregate_metrics_ref",
        "risk_budget_history",
        "fx_evidence_ids",
        "artifact_manifest",
    }
)
_COMPONENT_FIELDS = frozenset(
    {
        "component_id",
        "simulation_result_id",
        "journal_ref",
        "metrics_ref",
        "account_currency",
        "reconciled",
    }
)
_RETURN_FIELDS = frozenset({"component_id", "simulation_result_id", "observations"})
_OBSERVATION_FIELDS = frozenset({"timestamp", "return_value"})
_MIN_CORRELATION_SAMPLES = 30
_SHA256_HEX_LENGTH = 64
_MIN_PORTFOLIO_COMPONENTS = 2


def _require_sequence(value: object, field_name: str) -> tuple[object, ...]:
    """Validate one non-string sequence field.

    Args:
        value: Candidate sequence.
        field_name: Field used in controlled failures.

    Returns:
        Immutable sequence values.

    Raises:
        AnalyticsValidationError: If the field is not a sequence.
    """
    logger.debug("Validating Analytics allocation sequence")
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        message = f"{field_name} must be a sequence"
        raise AnalyticsValidationError(message)
    return tuple(value)


def _require_mapping(value: object, field_name: str) -> Mapping[str, object]:
    """Validate one mapping field.

    Args:
        value: Candidate mapping.
        field_name: Field used in controlled failures.

    Returns:
        Validated mapping.

    Raises:
        AnalyticsValidationError: If the field is not a mapping.
    """
    logger.debug("Validating Analytics allocation mapping")
    if not isinstance(value, Mapping):
        message = f"{field_name} must be a mapping"
        raise AnalyticsValidationError(message)
    return value


def _validated_component_pairs(
    rows: tuple[Mapping[str, object], ...],
) -> frozenset[tuple[str, str]]:
    """Validate exact reconciled component rows and return unique identities.

    Args:
        rows: Producer-owned component result rows.

    Returns:
        Unique component/result identity pairs.

    Raises:
        AnalyticsValidationError: If a row or identity is malformed or duplicated.
    """
    logger.debug("Validating Analytics allocation component rows")
    pairs: list[tuple[str, str]] = []
    for row in rows:
        if set(row) != _COMPONENT_FIELDS:
            raise AnalyticsValidationError("portfolio component row is invalid")
        component_id = row["component_id"]
        simulation_result_id = row["simulation_result_id"]
        text_values = (
            component_id,
            simulation_result_id,
            row["journal_ref"],
            row["metrics_ref"],
            row["account_currency"],
        )
        if (
            row["reconciled"] is not True
            or not isinstance(component_id, str)
            or not isinstance(simulation_result_id, str)
            or any(
                not isinstance(item, str) or not item or item != item.strip()
                for item in text_values
            )
        ):
            raise AnalyticsValidationError("portfolio component row is invalid")
        pairs.append((component_id, simulation_result_id))
    if len(set(pairs)) != len(pairs):
        raise AnalyticsValidationError("portfolio component identity is duplicated")
    return frozenset(pairs)


def _validate_portfolio_result(
    value: Mapping[str, object],
    *,
    base_currency: str,
) -> tuple[
    tuple[Mapping[str, object], ...],
    tuple[Mapping[str, object], ...],
    frozenset[tuple[str, str]],
]:
    """Validate the exact amended Simulation portfolio-result seam.

    Args:
        value: Producer-owned result mapping.
        base_currency: Requested Analytics base currency.

    Returns:
        Exact component rows, component-return rows, and component identities.

    Raises:
        AnalyticsValidationError: If identity, window, rows, or hashes are invalid.
    """
    logger.info("Validating Simulation portfolio result for Analytics allocation")
    if set(value) != _PORTFOLIO_RESULT_FIELDS:
        raise AnalyticsValidationError("portfolio simulation result fields mismatch")
    if (
        value["contract_version"] != "v1"
        or value["schema_id"] != "simulation.portfolio_result.v1"
        or value["status"] != "completed"
        or value["base_currency"] != base_currency
    ):
        raise AnalyticsValidationError("portfolio simulation result is incompatible")
    for name in ("request_hash", "config_hash", "data_hash", "result_hash"):
        digest = value[name]
        if (
            not isinstance(digest, str)
            or len(digest) != _SHA256_HEX_LENGTH
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise AnalyticsValidationError("portfolio simulation hash is invalid")
    start = value["measurement_start"]
    end = value["measurement_end"]
    if (
        not isinstance(start, datetime)
        or not isinstance(end, datetime)
        or start.tzinfo is None
        or end.tzinfo is None
        or start.utcoffset() != timedelta(0)
        or end.utcoffset() != timedelta(0)
        or end < start
    ):
        raise AnalyticsValidationError("portfolio simulation window is invalid")
    component_rows = tuple(
        _require_mapping(item, "component_result")
        for item in _require_sequence(value["component_results"], "component_results")
    )
    return_rows = tuple(
        _require_mapping(item, "component_return")
        for item in _require_sequence(
            value["component_return_series"], "component_return_series"
        )
    )
    if len(component_rows) < _MIN_PORTFOLIO_COMPONENTS or len(component_rows) != len(
        return_rows
    ):
        raise AnalyticsValidationError("portfolio component evidence is incomplete")
    component_pairs = _validated_component_pairs(component_rows)
    if any(set(row) != _RETURN_FIELDS for row in return_rows):
        raise AnalyticsValidationError("portfolio component return row is invalid")
    return component_rows, return_rows, component_pairs


def _return_maps(
    rows: tuple[Mapping[str, object], ...],
    *,
    measurement_start: datetime,
    measurement_end: datetime,
) -> dict[tuple[str, str], dict[datetime, float]]:
    """Validate exact return observations and index them by component/result pair.

    Args:
        rows: Exact component-return rows.
        measurement_start: Inclusive UTC window start.
        measurement_end: Inclusive UTC window end.

    Returns:
        Component/result keyed timestamp-return maps.

    Raises:
        AnalyticsValidationError: If observations are malformed or non-finite.
    """
    logger.debug("Indexing aligned Simulation component returns")
    result: dict[tuple[str, str], dict[datetime, float]] = {}
    for row in rows:
        component_id = row["component_id"]
        simulation_result_id = row["simulation_result_id"]
        if not isinstance(component_id, str) or not isinstance(
            simulation_result_id, str
        ):
            raise AnalyticsValidationError("component return identity is invalid")
        key = (component_id, simulation_result_id)
        if key in result:
            raise AnalyticsValidationError("duplicate component return evidence")
        observations: dict[datetime, float] = {}
        previous: datetime | None = None
        for item in _require_sequence(row["observations"], "observations"):
            observation = _require_mapping(item, "observation")
            if set(observation) != _OBSERVATION_FIELDS:
                raise AnalyticsValidationError("return observation fields mismatch")
            timestamp = observation["timestamp"]
            return_value = observation["return_value"]
            if (
                not isinstance(timestamp, datetime)
                or timestamp.tzinfo is None
                or timestamp.utcoffset() != timedelta(0)
                or not measurement_start <= timestamp <= measurement_end
                or (previous is not None and timestamp <= previous)
                or not isinstance(return_value, (int, float))
                or isinstance(return_value, bool)
                or not math.isfinite(float(return_value))
            ):
                raise AnalyticsValidationError("return observation is invalid")
            observations[timestamp] = float(return_value)
            previous = timestamp
        result[key] = observations
    return result


def _correlation(left: Sequence[float], right: Sequence[float]) -> float:
    """Calculate Pearson correlation for one aligned component pair.

    Args:
        left: Left component return values.
        right: Right component return values.

    Returns:
        Finite Pearson correlation.

    Raises:
        AnalyticsValidationError: If sample size or variance is insufficient.
    """
    logger.debug("Calculating Analytics component return correlation")
    if len(left) < _MIN_CORRELATION_SAMPLES or len(left) != len(right):
        raise AnalyticsValidationError("component return intersection is too short")
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    left_delta = tuple(value - left_mean for value in left)
    right_delta = tuple(value - right_mean for value in right)
    left_sum = sum(value * value for value in left_delta)
    right_sum = sum(value * value for value in right_delta)
    if left_sum == 0 or right_sum == 0:
        raise AnalyticsValidationError("component return variance is zero")
    value = sum(
        a * b for a, b in zip(left_delta, right_delta, strict=True)
    ) / math.sqrt(left_sum * right_sum)
    if not math.isfinite(value):
        raise AnalyticsValidationError("component correlation is non-finite")
    return value


def _dependence_section(
    return_maps: Mapping[tuple[str, str], Mapping[datetime, float]],
) -> SectionEvidence:
    """Build complete pairwise component dependence evidence.

    Args:
        return_maps: Validated timestamp-return maps.

    Returns:
        Completed dependence section.

    Raises:
        AnalyticsValidationError: If no component pair can be calculated.
    """
    logger.info("Building Analytics portfolio dependence evidence")
    entries = tuple(sorted(return_maps.items()))
    metrics: list[MetricEvidence] = []
    for index, ((left_component, _), left) in enumerate(entries):
        for (right_component, _), right in entries[index + 1 :]:
            intersection = tuple(sorted(set(left) & set(right)))
            value = _correlation(
                tuple(left[timestamp] for timestamp in intersection),
                tuple(right[timestamp] for timestamp in intersection),
            )
            metrics.append(
                MetricEvidence(
                    metric_key="component_return_correlation",
                    status="calculated",
                    value=value,
                    unit="ratio",
                    source_context=f"component_pair:{left_component}:{right_component}",
                )
            )
    if not metrics:
        raise AnalyticsValidationError("portfolio dependence evidence is empty")
    return SectionEvidence(
        section_key="dependence",
        criticality="required",
        metrics=tuple(metrics),
        status="completed",
    )


def _starting_equity(report: PerformanceReport) -> Decimal:
    """Extract one actual all-context component starting equity.

    Args:
        report: Component performance report.

    Returns:
        Positive exact starting equity.

    Raises:
        AnalyticsValidationError: If starting equity evidence is absent or invalid.
    """
    logger.debug("Extracting component starting equity for concentration")
    matches = tuple(
        metric
        for section in report.sections
        for metric in section.metrics
        if metric.metric_key == "starting_equity"
        and metric.source_context == "all"
        and metric.status == "calculated"
    )
    if (
        len(matches) != 1
        or not isinstance(matches[0].value, Decimal)
        or matches[0].value <= 0
    ):
        raise AnalyticsValidationError("component starting equity is invalid")
    return matches[0].value


def _concentration_section(
    reports: tuple[PerformanceReport, ...],
    *,
    base_currency: str,
    fx_evidence: Mapping[str, object] | None,
) -> tuple[SectionEvidence, tuple[Mapping[str, object], ...]]:
    """Build actual starting-capital HHI and component evidence.

    Args:
        reports: Ordered component reports.
        base_currency: Aggregate currency.
        fx_evidence: Exact Data-owned conversion evidence.

    Returns:
        Completed concentration section and component metrics.

    Raises:
        AnalyticsValidationError: If converted starting capital is invalid.
    """
    logger.info("Building Analytics portfolio concentration evidence")
    converted: list[tuple[PerformanceReport, Decimal, Decimal]] = []
    for report in reports:
        starting = _starting_equity(report)
        rate = _fx_rate(
            report.account_currency,
            base_currency,
            fx_evidence,
            evidence_time=report.created_at,
        )
        converted.append((report, starting, starting * rate))
    total = sum((item[2] for item in converted), Decimal(0))
    if total <= 0:
        raise AnalyticsValidationError("converted starting equity total is invalid")
    hhi = sum((float(item[2] / total) ** 2 for item in converted), 0.0)
    metric = MetricEvidence(
        metric_key="capital_concentration_hhi",
        status="calculated",
        value=hhi,
        unit="ratio",
        source_context="portfolio",
    )
    component_metrics = tuple(
        {
            "report_id": report.report_id,
            "source_result_id": report.lineage.source_ids[0],
            "account_currency": report.account_currency,
            "starting_equity": starting,
            "converted_starting_equity": converted_value,
            "capital_share": float(converted_value / total),
        }
        for report, starting, converted_value in converted
    )
    return (
        SectionEvidence(
            section_key="concentration",
            criticality="required",
            metrics=(metric,),
            status="completed",
        ),
        component_metrics,
    )


def build_portfolio_allocation_evidence(
    reports: Sequence[PerformanceReport],
    *,
    base_currency: str,
    fx_evidence: Mapping[str, object] | None,
    config: AnalyticsRunConfig,
    portfolio_simulation_result: Mapping[str, object],
) -> PortfolioAllocationEvidence:
    """Build complete non-binding allocation evidence from validated actual facts.

    Args:
        reports: Ordered component performance reports.
        base_currency: Required allocation evidence currency.
        fx_evidence: Caller-supplied Data-owned conversion evidence.
        config: Required component and response bounds.
        portfolio_simulation_result: Exact amended Simulation result mapping.

    Returns:
        Complete PortfolioAllocationEvidence v1.

    Raises:
        AnalyticsValidationError: If any source, pairing, FX, or metric fails.
    """
    logger.info("Building complete Analytics portfolio allocation evidence")
    components = tuple(reports)
    component_rows, return_rows, expected_pairs = _validate_portfolio_result(
        portfolio_simulation_result, base_currency=base_currency
    )
    if len(components) != len(component_rows):
        raise AnalyticsValidationError(
            "component report count does not match Simulation"
        )
    measurement_start = portfolio_simulation_result["measurement_start"]
    measurement_end = portfolio_simulation_result["measurement_end"]
    if not isinstance(measurement_start, datetime) or not isinstance(
        measurement_end, datetime
    ):
        raise AnalyticsValidationError("portfolio measurement window is invalid")
    observed_result_ids = {report.lineage.source_ids[0] for report in components}
    if observed_result_ids != {pair[1] for pair in expected_pairs}:
        raise AnalyticsValidationError("component report pairing is incompatible")
    currency_by_result = {
        str(row["simulation_result_id"]): row["account_currency"]
        for row in component_rows
    }
    if any(
        currency_by_result[report.lineage.source_ids[0]] != report.account_currency
        for report in components
    ):
        raise AnalyticsValidationError("component report currency is incompatible")
    if any(
        _measurement_window(report) != (measurement_start, measurement_end)
        for report in components
    ):
        raise AnalyticsValidationError("component measurement window does not match")
    portfolio = build_portfolio_performance_report(
        components,
        base_currency=base_currency,
        fx_evidence=fx_evidence,
        config=config,
    )
    return_maps = _return_maps(
        return_rows,
        measurement_start=measurement_start,
        measurement_end=measurement_end,
    )
    if set(return_maps) != expected_pairs:
        raise AnalyticsValidationError("component return pairing is incompatible")
    dependence = _dependence_section(return_maps)
    concentration, component_metrics = _concentration_section(
        components, base_currency=base_currency, fx_evidence=fx_evidence
    )
    identity_payload = {
        "portfolio_result_id": portfolio_simulation_result["result_id"],
        "report_ids": tuple(report.report_id for report in components),
        "dependence": dependence,
        "concentration": concentration,
    }
    evidence_id = hashlib.sha256(
        canonical_json(to_report_json_safe(identity_payload)).encode("utf-8")
    ).hexdigest()
    evidence = PortfolioAllocationEvidence(
        contract_version="v1",
        schema_id="analytics.portfolio_allocation_evidence.v1",
        evidence_id=evidence_id,
        allocation_reference=str(portfolio_simulation_result["construction_result_id"]),
        result_references=(
            str(portfolio_simulation_result["result_id"]),
            *(report.report_id for report in components),
        ),
        measurement_start=measurement_start,
        measurement_end=measurement_end,
        base_currency=base_currency,
        component_metrics=component_metrics,
        aggregate_metrics=portfolio.sections[0].metrics,
        dependence_evidence=dependence,
        concentration_evidence=concentration,
        caveats=portfolio.caveats,
        fx_lineage=portfolio.fx_lineage,
    )
    if (
        len(canonical_json(to_report_json_safe(evidence)).encode("utf-8"))
        > config.max_response_bytes
    ):
        raise AnalyticsValidationError("allocation evidence exceeds configured bound")
    logger.info("Completed Analytics portfolio allocation evidence")
    return evidence


def build_portfolio_rebalance_measurement(
    request: PortfolioRebalanceMeasurementRequest,
) -> PortfolioRebalanceMeasurementEvidence:
    """Build deterministic post-trade evidence from immutable Trading facts.

    Args:
        request: Validated receiver-owned measurement request.

    Returns:
        Deterministic non-binding measurement evidence.

    Raises:
        AnalyticsValidationError: If validated facts cannot be projected.
    """
    logger.info("Building deterministic Portfolio rebalance measurement")
    data = request.trading_facts.get("data")
    if not isinstance(data, Mapping):
        raise AnalyticsValidationError("Trading measurement data is unavailable")
    outcomes = data.get("outcomes")
    if not isinstance(outcomes, Sequence) or isinstance(outcomes, (str, bytes)):
        raise AnalyticsValidationError("Trading action outcomes are unavailable")
    measurements: list[Mapping[str, object]] = []
    for outcome in outcomes:
        if not isinstance(outcome, Mapping):
            raise AnalyticsValidationError("Trading action outcome is unavailable")
        measurements.append(
            {
                "action_id": str(outcome["action_id"]),
                "status": str(outcome["status"]),
            }
        )
    action_measurements = tuple(measurements)
    summary: Mapping[str, object] = {
        "execution_status": "success",
        "action_count": len(action_measurements),
        "successful_action_count": len(action_measurements),
    }
    material = {
        "contract_version": "v1",
        "schema_id": "analytics.portfolio_rebalance_measurement_evidence.v1",
        "evidence_id": f"{request.request_id}:evidence",
        "request_id": request.request_id,
        "workflow_id": request.workflow_id,
        "correlation_id": request.correlation_id,
        "portfolio_id": request.portfolio_id,
        "allocation_version": request.allocation_version,
        "plan_id": request.plan_id,
        "plan_version": request.plan_version,
        "plan_hash": request.plan_hash,
        "trading_request_id": request.trading_request_id,
        "trading_execution_ref": request.trading_execution_ref,
        "trading_execution_hash": request.trading_execution_hash,
        "action_measurements": action_measurements,
        "summary": summary,
        "measured_at": request.requested_at,
        "non_binding": True,
    }
    canonical_hash = hashlib.sha256(
        canonical_json(material).encode("utf-8")
    ).hexdigest()
    evidence = PortfolioRebalanceMeasurementEvidence(
        contract_version="v1",
        schema_id="analytics.portfolio_rebalance_measurement_evidence.v1",
        evidence_id=f"{request.request_id}:evidence",
        request_id=request.request_id,
        workflow_id=request.workflow_id,
        correlation_id=request.correlation_id,
        portfolio_id=request.portfolio_id,
        allocation_version=request.allocation_version,
        plan_id=request.plan_id,
        plan_version=request.plan_version,
        plan_hash=request.plan_hash,
        trading_request_id=request.trading_request_id,
        trading_execution_ref=request.trading_execution_ref,
        trading_execution_hash=request.trading_execution_hash,
        action_measurements=action_measurements,
        summary=summary,
        measured_at=request.requested_at,
        canonical_hash=canonical_hash,
        non_binding=True,
    )
    logger.info("Completed deterministic Portfolio rebalance measurement")
    return evidence


__all__ = [
    "build_portfolio_allocation_evidence",
    "build_portfolio_rebalance_measurement",
]
