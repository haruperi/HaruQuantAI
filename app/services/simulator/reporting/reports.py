"""Deterministic canonical JSON and Markdown Simulation reports."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.simulator.errors import SimulationError
from app.utils import ValidationError, canonical_json, logger

if TYPE_CHECKING:
    from app.services.simulator.reporting.contracts import SimulationResult


def build_json_report(result: SimulationResult) -> str:
    """Serialize a completed Simulation result deterministically.

    Args:
        result: Completed immutable result.

    Returns:
        Canonical JSON text.

    Raises:
        SimulationError: If canonical serialization fails.
    """
    logger.info("Building canonical JSON Simulation report")
    try:
        return canonical_json(result.model_dump(mode="python", warnings=False))
    except ValidationError as error:
        raise SimulationError(
            "SIM_INTERNAL_ERROR", "Result serialization failed"
        ) from error


def build_markdown_report(result: SimulationResult) -> str:
    """Render deterministic execution evidence without Analytics metrics.

    Args:
        result: Completed immutable result.

    Returns:
        Deterministic Markdown text.
    """
    logger.info("Building deterministic Markdown Simulation report")
    accounting = result.accounting
    lines = [
        "# Simulation Execution Report",
        "",
        f"- Run: `{result.run_id}`",
        f"- Status: `{result.status}`",
        f"- Engine: `{result.engine_version}`",
        f"- Data hash: `{result.data_hash}`",
        f"- Fills: {len(result.fills)}",
        f"- Closed trades: {len(result.closed_trades)}",
        f"- Initial balance: {result.initial_balance} {result.account_currency}",
        f"- Final balance: {accounting.final_balance} {result.account_currency}",
        f"- Commission: {accounting.commission}",
        f"- Swap: {accounting.swap}",
        "",
        "## Realism",
        "",
        f"- Tick model: `{result.realism.tick_model}`",
        f"- Slippage model: `{result.realism.slippage_model}`",
        f"- Liquidity model: `{result.realism.liquidity_model}`",
        f"- Session model: `{result.realism.session_model}`",
        f"- Data quality: `{result.realism.data_quality}`",
        "",
        "## Assumptions",
        "",
        *(f"- {item}" for item in result.realism.assumptions),
        "",
        "## Limitations",
        "",
        *(f"- {item}" for item in result.realism.limitations),
        "",
        f"Artifact manifest: `{result.artifact_manifest_ref}`",
        "",
    ]
    return "\n".join(lines)


__all__ = ["build_json_report", "build_markdown_report"]
