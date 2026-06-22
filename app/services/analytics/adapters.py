"""Deterministic trading result adapters for Analytics.

Converts raw backtest, paper, and live results into canonical TradingResult
dictionaries using the approved SCHEMA_COMPATIBILITY_MATRIX.  All conversion
is stateless and side-effect free.

Exports:
    TradingResultDict, BacktestResultDict, PaperTradingResultDict,
    LiveTradingResultDict, TradingResultAdapter, to_canonical.

Side effects:
    None.
"""

from __future__ import annotations

from typing import Any, TypedDict

from app.services.analytics.models import SCHEMA_COMPATIBILITY_MATRIX
from app.utils.errors import ValidationError

__all__ = [
    "BacktestResultDict",
    "LiveTradingResultDict",
    "PaperTradingResultDict",
    "TradingResultAdapter",
    "TradingResultDict",
    "to_canonical",
]

_VALID_PHASES = frozenset({"backtest", "paper", "live", "simulation"})

_ACCEPTED_STATUSES = frozenset(
    status
    for status, label in SCHEMA_COMPATIBILITY_MATRIX.items()
    if label in ("accepted", "deprecated", "legacy_adapted")
)


class TradingResultDict(TypedDict, total=False):
    """Canonical trading result contract.

    Required keys:
        schema_version: Analytics schema version string.
        result_id: Unique result identifier.
        phase: Trading phase (backtest / paper / live / simulation).
        trades: Chronological list of trade records.
        equity_curve: Chronological equity-curve records.

    Optional keys:
        strategy_id: Strategy name or identifier.
        strategy_version: Strategy version label.
        account_base_currency: ISO-4217 account currency.
        symbols: Traded symbol list.
        timeframe: Primary chart timeframe string.
        metadata: Arbitrary traceability metadata.
    """

    schema_version: str
    result_id: str
    phase: str
    trades: list[dict[str, Any]]
    equity_curve: list[dict[str, Any]]
    strategy_id: str
    strategy_version: str
    account_base_currency: str
    symbols: list[str]
    timeframe: str
    metadata: dict[str, Any]


class BacktestResultDict(TypedDict, total=False):
    """Backtest-specific trading result contract.

    Inherits all fields from TradingResultDict with phase constrained to
    ``"backtest"``.

    Required keys:
        schema_version, result_id, phase, trades, equity_curve.

    Optional keys:
        in_sample_end: ISO-8601 timestamp marking IS/OOS boundary.
        walk_forward_windows: List of walk-forward window descriptors.
    """

    schema_version: str
    result_id: str
    phase: str
    trades: list[dict[str, Any]]
    equity_curve: list[dict[str, Any]]
    in_sample_end: str
    walk_forward_windows: list[dict[str, Any]]


class PaperTradingResultDict(TypedDict, total=False):
    """Paper-trading-specific trading result contract.

    Required keys:
        schema_version, result_id, phase, trades, equity_curve.
    """

    schema_version: str
    result_id: str
    phase: str
    trades: list[dict[str, Any]]
    equity_curve: list[dict[str, Any]]


class LiveTradingResultDict(TypedDict, total=False):
    """Live-trading-specific trading result contract.

    Required keys:
        schema_version, result_id, phase, trades, equity_curve.
    """

    schema_version: str
    result_id: str
    phase: str
    trades: list[dict[str, Any]]
    equity_curve: list[dict[str, Any]]


# Backward-compatible plain-dict aliases kept for consumers that pre-date
# the TypedDict contract.
TradingResult = dict[str, Any]
BacktestResult = dict[str, Any]
PaperTradingResult = dict[str, Any]
LiveTradingResult = dict[str, Any]


class TradingResultAdapter:
    """Convert raw trading result payloads to the canonical schema.

    All methods are class-level; no instance state is required.  Conversion
    is stateless and produces no side effects.
    """

    REQUIRED_KEYS: frozenset[str] = frozenset(
        {
            "schema_version",
            "result_id",
            "phase",
            "trades",
            "equity_curve",
        }
    )

    @classmethod
    def _check_schema_version(cls, schema_version: str) -> list[str]:
        """Validate *schema_version* against SCHEMA_COMPATIBILITY_MATRIX.

        Args:
            schema_version: Version string from the raw payload.

        Returns:
            Warning strings to include in the canonical result metadata.

        Raises:
            ValidationError: When the version is rejected or unsupported.

        Side effects:
            None.
        """
        status = SCHEMA_COMPATIBILITY_MATRIX.get(schema_version)
        if status is None:
            if any(
                schema_version.startswith(k.rsplit(".", 1)[0])
                for k in SCHEMA_COMPATIBILITY_MATRIX
            ):
                return [
                    f"schema_version {schema_version!r} is not in the"
                    " compatibility matrix; treating as legacy_adapted."
                ]
            raise ValidationError(
                f"Unsupported schema version: {schema_version!r}."
                " Check SCHEMA_COMPATIBILITY_MATRIX for accepted versions."
            )
        if status == "rejected":
            raise ValidationError(
                f"Schema version {schema_version!r} is explicitly rejected."
            )
        if status == "unsupported_future":
            raise ValidationError(
                f"Schema version {schema_version!r} is a future version"
                " not yet supported by this engine."
            )
        warnings: list[str] = []
        if status == "deprecated":
            warnings.append(
                f"schema_version {schema_version!r} is deprecated."
                " Please migrate to a supported version."
            )
        if status == "legacy_adapted":
            warnings.append(
                f"schema_version {schema_version!r} requires legacy"
                " adaptation. Output may differ from accepted-version output."
            )
        return warnings

    @classmethod
    def to_canonical(
        cls,
        source_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Convert a raw result payload to a canonical TradingResultDict.

        Validates required keys, schema version compatibility, and field
        types.  Fills optional keys with documented defaults only when absent,
        and emits a ``_adapter_warnings`` list when defaults are applied to
        normally-required fields such as ``strategy_id``.

        Args:
            source_payload: Raw trading result dictionary.

        Returns:
            Canonical trading result dictionary.  The returned value always
            contains every required and optional key.  An
            ``_adapter_warnings`` key is added when the adapter applied
            defaults or encountered deprecated schema versions.

        Raises:
            ValidationError: When ``source_payload`` is not a dict, is
                missing required keys, or contains an incompatible schema
                version.

        Side effects:
            None.
        """
        if not isinstance(source_payload, dict):
            raise ValidationError(
                "Trading result source_payload must be a dictionary."
            )

        missing_keys = cls.REQUIRED_KEYS - source_payload.keys()
        if missing_keys:
            raise ValidationError(
                "Missing required keys for canonical TradingResult:"
                f" {sorted(missing_keys)}"
            )

        schema_version = source_payload.get("schema_version")
        if not isinstance(schema_version, str) or not schema_version.strip():
            raise ValidationError(
                "schema_version must be a non-empty string."
            )

        adapter_warnings = cls._check_schema_version(schema_version)

        result_id = source_payload.get("result_id")
        if not isinstance(result_id, str) or not result_id.strip():
            raise ValidationError(
                "result_id must be a non-empty string."
            )

        phase = source_payload.get("phase")
        if phase not in _VALID_PHASES:
            raise ValidationError(
                f"phase must be one of: {sorted(_VALID_PHASES)}"
            )

        trades = source_payload.get("trades")
        if not isinstance(trades, list):
            raise ValidationError("trades must be a list.")

        equity_curve = source_payload.get("equity_curve")
        if not isinstance(equity_curve, list):
            raise ValidationError("equity_curve must be a list.")

        canonical: dict[str, Any] = dict(source_payload)

        if "strategy_id" not in canonical:
            canonical["strategy_id"] = "default_strategy"
            adapter_warnings.append(
                "strategy_id was absent; defaulted to"
                " 'default_strategy'. Provide an explicit strategy_id"
                " for reproducible cross-run comparisons."
            )

        canonical.setdefault("strategy_version", "v1")
        canonical.setdefault("account_base_currency", "USD")
        canonical.setdefault("symbols", [])
        canonical.setdefault("timeframe", "H1")
        canonical.setdefault("metadata", {})

        if adapter_warnings:
            canonical["_adapter_warnings"] = adapter_warnings

        return canonical


def to_canonical(source_payload: dict[str, Any]) -> dict[str, Any]:
    """Module-level convenience wrapper for ``TradingResultAdapter.to_canonical``.

    Args:
        source_payload: Raw trading result dictionary.

    Returns:
        Canonical trading result dictionary.

    Raises:
        ValidationError: See ``TradingResultAdapter.to_canonical``.

    Side effects:
        None.
    """
    return TradingResultAdapter.to_canonical(source_payload)
