"""Cross-checks master settings and default acceptance conditions.

Description:
    Provides CrossChecksSettingsSnapshot and SettingsCrossChecksService
    managing enable/disable states, subjob-creation flags, and canonical
    default acceptance criteria for Walk Forward and SPP cross-checks.

Purpose:
    FEAT-RETESTER-CROSS-CHECKS: Master cross-checks snapshot and subjob dispatch.

Key Capabilities:
    - FR-retest-cross-checks-snapshot: Snapshot of all 9 robustness checks.
    - FR-retest-cross-checks-subjobs: Compute subjob creation flags for RetestPreflight.
    - FR-retest-cross-checks-defaults: Supply canonical default conditions.

Python API Usage:
    from app.workspace.retester.settings_cross_checks import (
        CrossChecksSettingsSnapshot,
        SettingsCrossChecksService,
    )
    snapshot = CrossChecksSettingsSnapshot(enabled=True)
    flags = SettingsCrossChecksService.creates_subjobs_flags(snapshot)

CLI Usage:
    python -m app.cli retest cross-checks --enabled true
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.core.host.logging import get_logger
from app.workspace.retester.preflight import RetestPreflight

logger = get_logger(__name__)

OperatorType = Literal["<", "<=", ">", ">=", "==", "!="]
FLOAT_TOLERANCE = 1e-9


@dataclass(frozen=True, slots=True)
class CrossCheckCondition:
    """Acceptance criterion for robustness checks."""

    name: str
    metric: str
    operator: OperatorType
    threshold: float
    is_enabled: bool = True

    def evaluate(self, actual_value: float) -> bool:
        """Evaluate actual value against condition threshold."""
        if not self.is_enabled:
            return True
        ops = {
            "<": actual_value < self.threshold,
            "<=": actual_value <= self.threshold,
            ">": actual_value > self.threshold,
            ">=": actual_value >= self.threshold,
            "==": abs(actual_value - self.threshold) < FLOAT_TOLERANCE,
            "!=": abs(actual_value - self.threshold) >= FLOAT_TOLERANCE,
        }
        return ops.get(self.operator, False)

    def to_dict(self) -> dict[str, Any]:
        """Convert condition to dictionary."""
        return {
            "name": self.name,
            "metric": self.metric,
            "operator": self.operator,
            "threshold": self.threshold,
            "is_enabled": self.is_enabled,
        }


@dataclass(frozen=True, slots=True)
class GenericCheckConfig:
    """Generic configuration wrapper for individual cross check options."""

    enabled: bool = False
    options: dict[str, Any] = field(default_factory=dict)
    acceptance_conditions: tuple[CrossCheckCondition, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "enabled": self.enabled,
            "options": dict(self.options),
            "acceptance_conditions": [c.to_dict() for c in self.acceptance_conditions],
        }


@dataclass(frozen=True, slots=True)
class CrossChecksSettingsSnapshot:
    """Snapshot of master settings across all 9 robustness cross-check plugins."""

    enabled: bool = False
    what_if: GenericCheckConfig = field(default_factory=GenericCheckConfig)
    higher_precision: GenericCheckConfig = field(default_factory=GenericCheckConfig)
    additional_markets: GenericCheckConfig = field(default_factory=GenericCheckConfig)
    mc_manipulation: GenericCheckConfig = field(default_factory=GenericCheckConfig)
    mc_retest: GenericCheckConfig = field(default_factory=GenericCheckConfig)
    opt_profile_spp: GenericCheckConfig = field(default_factory=GenericCheckConfig)
    sequential_opt: GenericCheckConfig = field(default_factory=GenericCheckConfig)
    wf_optimization: GenericCheckConfig = field(default_factory=GenericCheckConfig)
    wf_matrix: GenericCheckConfig = field(default_factory=GenericCheckConfig)

    def to_dict(self) -> dict[str, Any]:
        """Convert snapshot to dictionary representation."""
        return {
            "enabled": self.enabled,
            "what_if": self.what_if.to_dict(),
            "higher_precision": self.higher_precision.to_dict(),
            "additional_markets": self.additional_markets.to_dict(),
            "mc_manipulation": self.mc_manipulation.to_dict(),
            "mc_retest": self.mc_retest.to_dict(),
            "opt_profile_spp": self.opt_profile_spp.to_dict(),
            "sequential_opt": self.sequential_opt.to_dict(),
            "wf_optimization": self.wf_optimization.to_dict(),
            "wf_matrix": self.wf_matrix.to_dict(),
        }


class SettingsCrossChecksService:
    """Service providing subjob resolution and default condition palettes."""

    @staticmethod
    def creates_subjobs_flags(
        snapshot: CrossChecksSettingsSnapshot,
    ) -> tuple[bool, ...]:
        """Extract tuple of boolean flags for checks that create independent subjobs.

        Cross-checks that create subjobs when enabled:
        - Monte Carlo Retest
        - Higher Precision
        - Additional Markets
        - Sequential Optimization
        - Walk Forward Optimization
        - Walk Forward Matrix
        - System Parameter Permutation (SPP)

        Args:
            snapshot: Master cross-checks settings.

        Returns:
            Tuple of booleans corresponding to active subjob-producing checks.
        """
        subjob_flags = (
            bool(snapshot.mc_retest.enabled),
            bool(snapshot.higher_precision.enabled),
            bool(snapshot.additional_markets.enabled),
            bool(snapshot.sequential_opt.enabled),
            bool(snapshot.wf_optimization.enabled),
            bool(snapshot.wf_matrix.enabled),
            bool(snapshot.opt_profile_spp.enabled),
        )
        logger.info(
            "FR-retest-cross-checks-subjobs: evaluated %d subjob flags (active=%d)",
            len(subjob_flags),
            sum(1 for f in subjob_flags if f),
        )
        return subjob_flags

    @staticmethod
    def resolve_mode(snapshot: CrossChecksSettingsSnapshot) -> int:
        """Resolve backtest mode using RetestPreflight.

        Args:
            snapshot: Master cross-checks settings.

        Returns:
            0 if cross-checks are enabled and at least one creates subjobs, else 1.
        """
        flags = SettingsCrossChecksService.creates_subjobs_flags(snapshot)
        return RetestPreflight.mode(
            cross_checks_enabled=snapshot.enabled,
            creates_subjobs=flags,
        )

    @staticmethod
    def get_default_wf_conditions() -> tuple[CrossCheckCondition, ...]:
        """Return default acceptance conditions for Walk Forward."""
        return (
            CrossCheckCondition(
                name="ProfitableRuns",
                metric="ProfitableRunsPct",
                operator=">=",
                threshold=70.0,
            ),
            CrossCheckCondition(
                name="WFEfficiency",
                metric="WFEfficiencyPct",
                operator=">=",
                threshold=50.0,
            ),
        )

    @staticmethod
    def get_default_spp_conditions() -> tuple[CrossCheckCondition, ...]:
        """Return default acceptance conditions for System Parameter Permutation."""
        return (
            CrossCheckCondition(
                name="ProfitableRuns",
                metric="ProfitableRunsPct",
                operator=">=",
                threshold=70.0,
            ),
            CrossCheckCondition(
                name="ParameterStability",
                metric="StabilityScore",
                operator=">=",
                threshold=60.0,
            ),
        )
