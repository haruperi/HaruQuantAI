"""Dashboard payload builders for Analytics UI/API representation.

Projects validated report sections into bounded chart/table payloads.
All calculations are stateless pure functions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from app.services.analytics.dashboards.truncation import (
    TruncationPolicy,
    truncate_series,
)
from app.services.analytics.errors import AnalyticsValidationError as ValidationError
from app.utils import (
    StandardResponse,
    build_metadata,
    response_from_exception,
    success_response,
)
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.analytics.reports.sections import AnalyticsReport


@dataclass(frozen=True, slots=True)
class DashboardConfig:
    """Configuration options for API and UI dashboard generation.

    Args:
        max_points: Limits the maximum number of datapoints in resampled charts.
    """

    max_points: int = 100


@dataclass(frozen=True, slots=True)
class TruncationMetadata:
    """Preserved metadata describing the downsample / truncation details.

    Args:
        truncated: True if points count was reduced.
        original_count: Pre-truncated size.
        returned_count: Post-truncated size.
        truncation_method: The downsampling algorithm name.
        truncation_reason: Cause description for the downsample trigger.
    """

    truncated: bool
    original_count: int
    returned_count: int
    truncation_method: str | None
    truncation_reason: str | None


@dataclass(frozen=True, slots=True)
class DashboardPayload:
    """Structured UI overview presentation schema payload.

    Args:
        schema_version: Interface contract version.
        charts: Chart objects container.
        tables: Data tables container.
        truncation: Associated truncation details.
    """

    schema_version: str = "1.3.1"
    charts: dict[str, Any] = field(default_factory=dict)
    tables: dict[str, Any] = field(default_factory=dict)
    truncation: TruncationMetadata = field(
        default_factory=lambda: TruncationMetadata(
            truncated=False,
            original_count=0,
            returned_count=0,
            truncation_method=None,
            truncation_reason=None,
        )
    )


def _validate_request_id(request_id: str | None) -> None:
    """Helper to validate request_id strictly.

    Args:
        request_id (str | None): Input parameter `request_id`.
    """
    logger.debug("_validate_request_id: executed.")
    if request_id is not None and (
        not isinstance(request_id, str) or not request_id.strip()
    ):
        raise ValidationError("request_id must be a non-empty string.")


def build_overview_payload(
    report: AnalyticsReport | dict[str, Any] | None,
    config: DashboardConfig | str | None = None,
    request_id: str | None = None,
) -> StandardResponse | DashboardPayload:
    """Format a report into UI cards, tables, and downsampled curves.

    Args:
        report (AnalyticsReport | dict[str, Any] | None): Input parameter `report`.
        config (DashboardConfig | str | None): Metric configuration.
        request_id (str | None): Input parameter `request_id`.

    Returns:
        Calculated StandardResponse | DashboardPayload value.
    """
    logger.debug("build_overview_payload: executed.")
    if isinstance(config, str):
        request_id = config
        config = None

    _validate_request_id(request_id)
    meta = build_metadata(
        tool_name="build_overview_payload",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        if report is None:
            return response_from_exception(
                exception=ValidationError("report must not be None."),
                metadata=meta,
            )
        if not isinstance(report, dict) and not hasattr(report, "sections"):
            return response_from_exception(
                exception=ValidationError(
                    "report must be a dictionary or have a sections attribute."
                ),
                metadata=meta,
            )

        cfg = config or DashboardConfig()
        sections: dict[str, Any] = {}
        if isinstance(report, dict):
            sections = report.get("sections") or report
        else:
            sections = report.sections

        trade_sec = sections.get("trade_metrics") or sections.get("trade") or {}
        ratio_sec = sections.get("ratio_metrics") or sections.get("ratios") or {}
        dd_sec = sections.get("drawdown_metrics") or sections.get("drawdown") or {}
        eq_sec = sections.get("equity_metrics") or sections.get("equity") or {}

        summary_cards = {
            "net_profit": float(
                eq_sec.get("data", {}).get("total_return_usd", 0.0)
                if "data" in eq_sec
                else eq_sec.get("total_return_usd", 0.0)
            ),
            "win_rate": float(
                trade_sec.get("data", {}).get("win_rate", 0.0)
                if "data" in trade_sec
                else trade_sec.get("win_rate", 0.0)
            ),
            "profit_factor": float(
                ratio_sec.get("data", {}).get("profit_factor", 1.0)
                if "data" in ratio_sec
                else ratio_sec.get("profit_factor", 1.0)
            ),
            "max_drawdown_percent": float(
                dd_sec.get("data", {}).get("max_drawdown_percent", 0.0)
                if "data" in dd_sec
                else dd_sec.get("max_drawdown_percent", 0.0)
            ),
            "sharpe_ratio": float(
                ratio_sec.get("data", {}).get("sharpe_ratio", 0.0)
                if "data" in ratio_sec
                else ratio_sec.get("sharpe_ratio", 0.0)
            ),
            "total_trades": int(
                trade_sec.get("data", {}).get("total_trades", 0)
                if "data" in trade_sec
                else trade_sec.get("total_trades", 0)
            ),
        }

        raw_curve: list[Any] = []
        if isinstance(report, dict):
            raw_curve = report.get("equity_curve") or []
        else:
            raw_curve = getattr(report, "equity_curve", [])

        truncated_res = truncate_series(
            raw_curve, TruncationPolicy(max_points=cfg.max_points)
        )
        downsampled_equity = {
            "curve": truncated_res.curve,
            "truncated": truncated_res.truncated,
            "original_count": truncated_res.original_count,
            "returned_count": truncated_res.returned_count,
            "truncation_method": truncated_res.truncation_method,
            "truncation_reason": truncated_res.truncation_reason,
        }

        warnings = []
        q_flags = []
        if isinstance(report, dict):
            warnings = report.get("warnings", [])
            q_flags = report.get("quality_flags", [])
        else:
            warnings = getattr(report, "warnings", [])
            q_flags = getattr(report, "quality_flags", [])

        if config is not None:
            return DashboardPayload(
                schema_version="1.3.1",
                charts={"equity_curve": downsampled_equity},
                tables={
                    "summary_cards": summary_cards,
                    "warnings": warnings,
                    "quality_flags": q_flags,
                },
                truncation=TruncationMetadata(
                    truncated=truncated_res.truncated,
                    original_count=truncated_res.original_count,
                    returned_count=truncated_res.returned_count,
                    truncation_method=truncated_res.truncation_method,
                    truncation_reason=truncated_res.truncation_reason,
                ),
            )

        data = {
            "summary_cards": summary_cards,
            "equity_curve_chart": downsampled_equity,
            "monthly_heatmap": {},
            "warnings": warnings,
            "quality_flags": q_flags,
        }

        return success_response(
            message="Dashboard overview payload built successfully.",
            data=data,
            metadata=meta,
        )
    except Exception as e:  # noqa: BLE001
        return response_from_exception(exception=e, metadata=meta)
