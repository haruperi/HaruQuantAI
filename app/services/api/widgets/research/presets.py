"""Server-owned Research presets and safe override resolution.

A browser never chooses an artifact root, a resource ceiling, or a raw
``EdgeLabConfig``. It chooses a named preset plus a bounded set of approved
overrides; this module turns that choice into the complete Research-owned
configuration. Every ceiling below is gateway policy, not caller input.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, cast

from app.services.research import create_research_value
from app.utils import get_logger

if TYPE_CHECKING:
    from app.services.api.widgets.research.schemas import ResearchRunCreateRequest

logger = get_logger(__name__)

type JsonValue = Any

#: Canonical Research stage vocabulary, in dependency order.
RESEARCH_STAGES: Final[tuple[str, ...]] = (
    "data",
    "features",
    "leakage",
    "metrics",
    "statistics",
    "studies",
    "seasonality",
    "market_structure",
    "modeling",
    "profiles",
)

#: Stages every run must include, because preparation is the run's foundation.
REQUIRED_STAGES: Final[tuple[str, ...]] = ("data",)

#: Gateway-owned artifact root. Never caller-supplied.
_ARTIFACT_ROOT: Final[Path] = Path("artifacts/research")

#: Gateway-owned resource ceilings applied to every browser-initiated run.
_MAX_ROWS: Final[int] = 200_000
_MAX_DURATION_SECONDS: Final[float] = 300.0
_MAX_ARTIFACT_BYTES: Final[int] = 10_485_760
_MEMORY_BUDGET_MB: Final[int] = 512

#: Bounds applied to approved statistical overrides.
_MAX_SAMPLES: Final[int] = 2_000
_MIN_SAMPLES: Final[int] = 20
_MAX_WINDOW: Final[int] = 512
_MAX_HORIZON: Final[int] = 256
_MAX_FEATURE_WINDOWS: Final[int] = 8
_MAX_FORWARD_HORIZONS: Final[int] = 4
_MAX_CLUSTERS: Final[int] = 12
_MIN_CLUSTERS: Final[int] = 2

#: Default named session windows shared by every preset.
_SESSION_WINDOWS: Final[Mapping[str, tuple[time, time]]] = {
    "sydney": (time(21, 0), time(6, 0)),
    "tokyo": (time(0, 0), time(9, 0)),
    "london": (time(7, 0), time(16, 0)),
    "new_york": (time(12, 0), time(21, 0)),
}
_SESSION_PRECEDENCE: Final[tuple[str, ...]] = (
    "london",
    "new_york",
    "tokyo",
    "sydney",
)

#: Keys the browser may override. Anything else is rejected as unsupported.
APPROVED_OVERRIDE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "seed",
        "bootstrap_samples",
        "permutation_samples",
        "null_samples",
        "block_size",
        "correction",
        "feature_windows",
        "forward_horizons",
        "continue_on_study_error",
        "enable_market_structure_quality",
        "validation_horizon",
        "calibration_candidates",
        "modeling_clusters",
        "modeling_pca_components",
        "session_timezone",
    }
)


class PresetError(ValueError):
    """One rejected preset selection or unsupported override."""


_PRESETS: Final[tuple[Mapping[str, JsonValue], ...]] = (
    {
        "preset_id": "quick_look",
        "name": "Quick Look",
        "description": (
            "Fast orientation pass: preparation, metric families, and "
            "seasonality only. No statistical claims are produced."
        ),
        "selected_stages": ("data", "metrics", "seasonality"),
        "statistics": {
            "seed": 7,
            "bootstrap_samples": 200,
            "permutation_samples": 200,
            "block_size": 8,
            "null_samples": 200,
            "correction": None,
        },
        "studies": {
            "mean_reversion": {
                "lookback": 20,
                "entry_zscore": 2.0,
                "hold_bars": 5,
                "side": "buy",
                "minimum_samples": 30,
                "q": 0.95,
                "null_quantile": 0.95,
            },
            "trend_persistence": {
                "lookback": 20,
                "minimum_move": 0.5,
                "hold_bars": 5,
                "side": "buy",
                "minimum_samples": 30,
                "q": 0.95,
                "null_quantile": 0.95,
            },
            "session": {
                "horizon": 4,
                "minimum_samples": 30,
                "q": 0.95,
                "null_quantile": 0.95,
            },
        },
        "feature_windows": {"sma": 20, "atr": 14},
        "forward_horizons": (1,),
        "enable_market_structure_quality": False,
        "validation_horizon": 20,
        "calibration_candidates": 8,
        "modeling_clusters": 3,
        "modeling_pca_components": 2,
        "continue_on_study_error": True,
    },
    {
        "preset_id": "standard_edge",
        "name": "Standard Edge Study",
        "description": (
            "Default workbench pass: features, leakage review, metrics, seeded "
            "statistics, the three edge studies, seasonality, market structure, "
            "and the scorecard."
        ),
        "selected_stages": RESEARCH_STAGES,
        "statistics": {
            "seed": 7,
            "bootstrap_samples": 500,
            "permutation_samples": 500,
            "block_size": 16,
            "null_samples": 500,
            "correction": "benjamini_hochberg",
        },
        "studies": {
            "mean_reversion": {
                "lookback": 20,
                "entry_zscore": 2.0,
                "hold_bars": 5,
                "side": "buy",
                "minimum_samples": 30,
                "q": 0.95,
                "null_quantile": 0.95,
            },
            "trend_persistence": {
                "lookback": 20,
                "minimum_move": 0.5,
                "hold_bars": 5,
                "side": "buy",
                "minimum_samples": 30,
                "q": 0.95,
                "null_quantile": 0.95,
            },
            "session": {
                "horizon": 4,
                "minimum_samples": 30,
                "q": 0.95,
                "null_quantile": 0.95,
            },
        },
        "feature_windows": {"sma": 20, "atr": 14, "zscore": 50},
        "forward_horizons": (1, 5),
        "enable_market_structure_quality": True,
        "validation_horizon": 24,
        "calibration_candidates": 16,
        "modeling_clusters": 4,
        "modeling_pca_components": 3,
        "continue_on_study_error": True,
    },
    {
        "preset_id": "deep_validation",
        "name": "Deep Validation",
        "description": (
            "Highest-evidence pass: larger seeded resample counts, "
            "multiple-testing correction, market-structure quality evidence, "
            "and strict study failure policy."
        ),
        "selected_stages": RESEARCH_STAGES,
        "statistics": {
            "seed": 7,
            "bootstrap_samples": 2_000,
            "permutation_samples": 2_000,
            "block_size": 24,
            "null_samples": 2_000,
            "correction": "benjamini_hochberg",
        },
        "studies": {
            "mean_reversion": {
                "lookback": 20,
                "entry_zscore": 2.0,
                "hold_bars": 5,
                "side": "buy",
                "minimum_samples": 60,
                "q": 0.99,
                "null_quantile": 0.99,
            },
            "trend_persistence": {
                "lookback": 20,
                "minimum_move": 0.5,
                "hold_bars": 5,
                "side": "buy",
                "minimum_samples": 60,
                "q": 0.99,
                "null_quantile": 0.99,
            },
            "session": {
                "horizon": 4,
                "minimum_samples": 60,
                "q": 0.99,
                "null_quantile": 0.99,
            },
        },
        "feature_windows": {"sma": 20, "atr": 14, "zscore": 50, "hurst": 100},
        "forward_horizons": (1, 5, 20),
        "enable_market_structure_quality": True,
        "validation_horizon": 48,
        "calibration_candidates": 32,
        "modeling_clusters": 5,
        "modeling_pca_components": 3,
        "continue_on_study_error": False,
    },
)

_PRESETS_BY_ID: Final[Mapping[str, Mapping[str, JsonValue]]] = {
    str(preset["preset_id"]): preset for preset in _PRESETS
}


def list_research_presets() -> tuple[Mapping[str, JsonValue], ...]:
    """Return every server-owned preset as browser-safe evidence.

    Returns:
        Immutable preset summaries including their selected stages and the
        approved override keys a caller may supply.
    """
    logger.debug("Listing server-owned Research presets")
    return tuple(
        {
            "preset_id": str(preset["preset_id"]),
            "name": str(preset["name"]),
            "description": str(preset["description"]),
            "selected_stages": list(cast("Sequence[str]", preset["selected_stages"])),
            "statistics": dict(cast("Mapping[str, object]", preset["statistics"])),
            "feature_windows": dict(
                cast("Mapping[str, int]", preset["feature_windows"])
            ),
            "forward_horizons": list(cast("Sequence[int]", preset["forward_horizons"])),
            "enable_market_structure_quality": bool(
                preset["enable_market_structure_quality"]
            ),
            "modeling_clusters": int(cast("int", preset["modeling_clusters"])),
            "modeling_pca_components": int(
                cast("int", preset["modeling_pca_components"])
            ),
            "studies": {
                name: dict(cast("Mapping[str, object]", settings))
                for name, settings in cast(
                    "Mapping[str, object]", preset["studies"]
                ).items()
            },
            "continue_on_study_error": bool(preset["continue_on_study_error"]),
            "approved_override_keys": sorted(APPROVED_OVERRIDE_KEYS),
        }
        for preset in _PRESETS
    )


def get_stage_vocabulary() -> tuple[str, ...]:
    """Return the canonical selectable Research stage vocabulary.

    Returns:
        Stage names in dependency order.
    """
    return RESEARCH_STAGES


def _bounded_int(value: object, *, low: int, high: int, detail: str) -> int:
    """Coerce one override into a bounded integer.

    Args:
        value: Caller-supplied override value.
        low: Inclusive lower bound.
        high: Inclusive upper bound.
        detail: Symbolic rejection detail.

    Returns:
        The bounded integer.

    Raises:
        PresetError: If the value is not an integer inside the bound.
    """
    try:
        number = int(cast("int", value))
    except (TypeError, ValueError) as error:
        raise PresetError(detail) from error
    if not low <= number <= high:
        raise PresetError(detail)
    return number


def _resolved_statistics(
    preset: Mapping[str, JsonValue],
    overrides: Mapping[str, object],
) -> Mapping[str, object]:
    """Apply approved statistical overrides inside gateway ceilings.

    Args:
        preset: Selected server-owned preset.
        overrides: Approved caller overrides.

    Returns:
        Complete statistical settings.

    Raises:
        PresetError: If an override is outside the approved range.
    """
    values = dict(cast("Mapping[str, object]", preset["statistics"]))
    for key in ("bootstrap_samples", "permutation_samples", "null_samples"):
        if key in overrides:
            values[key] = _bounded_int(
                overrides[key],
                low=_MIN_SAMPLES,
                high=_MAX_SAMPLES,
                detail="SAMPLE_COUNT_OUT_OF_RANGE",
            )
    if "seed" in overrides:
        values["seed"] = _bounded_int(
            overrides["seed"], low=0, high=2**31 - 1, detail="SEED_OUT_OF_RANGE"
        )
    if "block_size" in overrides:
        values["block_size"] = _bounded_int(
            overrides["block_size"],
            low=1,
            high=256,
            detail="BLOCK_SIZE_OUT_OF_RANGE",
        )
    if "correction" in overrides:
        correction = overrides["correction"]
        if correction not in {None, "", "benjamini_hochberg"}:
            raise PresetError("CORRECTION_UNSUPPORTED")
        values["correction"] = correction or None
    return values


def _resolved_windows(
    preset: Mapping[str, JsonValue],
    overrides: Mapping[str, object],
) -> tuple[Mapping[str, int], tuple[int, ...]]:
    """Apply approved feature-window and forward-horizon overrides.

    Args:
        preset: Selected server-owned preset.
        overrides: Approved caller overrides.

    Returns:
        Feature windows and forward horizons.

    Raises:
        PresetError: If a window or horizon is invalid or unbounded.
    """
    windows = dict(cast("Mapping[str, int]", preset["feature_windows"]))
    horizons = tuple(cast("Sequence[int]", preset["forward_horizons"]))
    if "feature_windows" in overrides:
        supplied = overrides["feature_windows"]
        if not isinstance(supplied, Mapping) or not supplied:
            raise PresetError("FEATURE_WINDOWS_INVALID")
        if len(supplied) > _MAX_FEATURE_WINDOWS:
            raise PresetError("TOO_MANY_FEATURE_WINDOWS")
        windows = {
            str(name): _bounded_int(
                value, low=2, high=_MAX_WINDOW, detail="FEATURE_WINDOW_OUT_OF_RANGE"
            )
            for name, value in supplied.items()
        }
    if "forward_horizons" in overrides:
        supplied_horizons = overrides["forward_horizons"]
        if not isinstance(supplied_horizons, Sequence) or isinstance(
            supplied_horizons, str | bytes
        ):
            raise PresetError("FORWARD_HORIZONS_INVALID")
        if not supplied_horizons or len(supplied_horizons) > _MAX_FORWARD_HORIZONS:
            raise PresetError("FORWARD_HORIZONS_INVALID")
        horizons = tuple(
            _bounded_int(
                value, low=1, high=_MAX_HORIZON, detail="FORWARD_HORIZON_OUT_OF_RANGE"
            )
            for value in supplied_horizons
        )
        if len(set(horizons)) != len(horizons):
            raise PresetError("FORWARD_HORIZON_DUPLICATED")
    return windows, horizons


def resolve_selected_stages(
    preset_id: str,
    selected: Sequence[str] | None,
) -> tuple[str, ...]:
    """Resolve the exact stage selection for one run.

    Args:
        preset_id: Selected server-owned preset identifier.
        selected: Optional caller stage subset.

    Returns:
        Ordered, dependency-complete stage selection.

    Raises:
        PresetError: If the preset or a named stage is unknown.
    """
    preset = _PRESETS_BY_ID.get(preset_id)
    if preset is None:
        raise PresetError("PRESET_UNKNOWN")
    available = tuple(cast("Sequence[str]", preset["selected_stages"]))
    if not selected:
        return available
    requested = set(selected)
    if requested - set(RESEARCH_STAGES):
        raise PresetError("STAGE_UNKNOWN")
    requested.update(REQUIRED_STAGES)
    # Dependency closure mirrors the Research workflow's own stage contract, so
    # a caller can select "studies" without knowing it needs safe features.
    if "leakage" in requested:
        requested.add("features")
    if "studies" in requested:
        requested.update({"features", "leakage"})
    if "modeling" in requested:
        requested.add("features")
    if "profiles" in requested:
        requested.add("metrics")
    return tuple(stage for stage in RESEARCH_STAGES if stage in requested)


def build_preset_config(
    request: ResearchRunCreateRequest,
    *,
    symbol: str,
    selected_stages: Sequence[str],
    artifact_root: Path | None = None,
) -> object:
    """Build the complete Research configuration for one browser-safe request.

    Args:
        request: Validated safe run-create request.
        symbol: Canonical symbol resolved from the Data dataset.
        selected_stages: Dependency-complete stage selection.
        artifact_root: Optional gateway-owned override used by tests.

    Returns:
        Opaque Research-owned ``EdgeLabConfig``.

    Raises:
        PresetError: If the preset or any approved override is invalid.
    """
    preset = _PRESETS_BY_ID.get(request.preset)
    if preset is None:
        raise PresetError("PRESET_UNKNOWN")
    overrides = dict(request.approved_overrides)
    unsupported = set(overrides) - APPROVED_OVERRIDE_KEYS
    if unsupported:
        logger.warning("Rejecting unsupported Research overrides")
        raise PresetError("OVERRIDE_UNSUPPORTED")
    if request.seed is not None:
        overrides["seed"] = request.seed

    statistics = _resolved_statistics(preset, overrides)
    windows, horizons = _resolved_windows(preset, overrides)
    clusters = (
        _bounded_int(
            overrides["modeling_clusters"],
            low=_MIN_CLUSTERS,
            high=_MAX_CLUSTERS,
            detail="CLUSTER_COUNT_OUT_OF_RANGE",
        )
        if "modeling_clusters" in overrides
        else int(cast("int", preset["modeling_clusters"]))
    )
    components = (
        _bounded_int(
            overrides["modeling_pca_components"],
            low=1,
            high=4,
            detail="PCA_COMPONENT_OUT_OF_RANGE",
        )
        if "modeling_pca_components" in overrides
        else int(cast("int", preset["modeling_pca_components"]))
    )
    quality = bool(
        overrides.get(
            "enable_market_structure_quality",
            preset["enable_market_structure_quality"],
        )
    )
    validation_horizon = (
        _bounded_int(
            overrides["validation_horizon"],
            low=1,
            high=_MAX_WINDOW,
            detail="VALIDATION_HORIZON_OUT_OF_RANGE",
        )
        if "validation_horizon" in overrides
        else int(cast("int", preset["validation_horizon"]))
    )
    calibration = (
        _bounded_int(
            overrides["calibration_candidates"],
            low=1,
            high=64,
            detail="CALIBRATION_COUNT_OUT_OF_RANGE",
        )
        if "calibration_candidates" in overrides
        else int(cast("int", preset["calibration_candidates"]))
    )
    timezone = str(overrides.get("session_timezone", "UTC")) or "UTC"
    continue_on_error = bool(
        overrides.get("continue_on_study_error", preset["continue_on_study_error"])
    )
    modeling_features = ("close", "volume", "spread")[: max(components, 2)]
    if len(modeling_features) < components:
        modeling_features = ("close", "volume", "spread")

    return create_research_value(
        "EdgeLabConfig",
        cleaning=create_research_value(
            "CleaningConfig",
            timezone=timezone,
            duplicate_strategy="keep_last",
            missing_bar_strategy="none",
            non_trading_period_strategy="keep_warn",
            spread_strategy="keep_warn",
        ),
        enrichment=create_research_value(
            "EnrichmentConfig",
            symbol=symbol,
            include_geometry=True,
            include_returns=True,
            include_forward_labels=True,
            include_calendar=True,
        ),
        features=create_research_value(
            "FeatureConfig",
            windows=windows,
            forward_horizons=horizons,
            allowed_forward_columns=tuple(
                f"forward_return_{horizon}" for horizon in horizons
            ),
            nan_policy="preserve",
        ),
        statistics=create_research_value("StatisticalConfig", **statistics),
        studies=create_research_value(
            "StudyConfig",
            mean_reversion=dict(
                cast("Mapping[str, Mapping[str, JsonValue]]", preset["studies"])[
                    "mean_reversion"
                ]
            ),
            trend_persistence=dict(
                cast("Mapping[str, Mapping[str, JsonValue]]", preset["studies"])[
                    "trend_persistence"
                ]
            ),
            session=dict(
                cast("Mapping[str, Mapping[str, JsonValue]]", preset["studies"])[
                    "session"
                ]
            ),
            continue_on_study_error=continue_on_error,
        ),
        sessions=create_research_value(
            "SessionConfig",
            timezone=timezone,
            windows=dict(_SESSION_WINDOWS),
            overlap_precedence=_SESSION_PRECEDENCE,
        ),
        market_structure=create_research_value(
            "MarketStructureConfig",
            profile={},
            enable_quality=quality,
            quality_windows=(20, 50),
            calibration_candidates=calibration,
            validation_horizon=validation_horizon,
        ),
        modeling=create_research_value(
            "UnsupervisedResearchConfig",
            feature_columns=modeling_features,
            scale=True,
            pca_components=min(components, len(modeling_features)),
            clusters=clusters,
            minimum_samples=max(20, 10 * clusters, 2 * components),
            seed=int(cast("int", statistics["seed"])),
        ),
        artifacts=create_research_value(
            "ArtifactWriteConfig",
            allowed_root=(artifact_root or _ARTIFACT_ROOT).resolve(),
            format="json",
            overwrite=True,
        ),
        limits=create_research_value(
            "ResearchResourceLimits",
            max_rows=_MAX_ROWS,
            max_duration_seconds=_MAX_DURATION_SECONDS,
            max_artifact_bytes=_MAX_ARTIFACT_BYTES,
            memory_budget_mb=_MEMORY_BUDGET_MB,
        ),
        selected_stages=tuple(selected_stages),
    )


def get_artifact_root() -> Path:
    """Return the gateway-owned Research artifact root.

    Returns:
        Absolute artifact directory chosen by the server, never the browser.
    """
    return _ARTIFACT_ROOT.resolve()


def describe_effective_configuration(config: object) -> Mapping[str, JsonValue]:
    """Project one resolved configuration into browser-safe evidence.

    Filesystem roots and resource ceilings are deliberately excluded: they are
    server decisions and must never round-trip through a browser.

    Args:
        config: Resolved Research configuration.

    Returns:
        JSON-safe effective configuration evidence.
    """
    typed = cast("Any", config)
    return {
        "selected_stages": [str(stage) for stage in typed.selected_stages],
        "session_timezone": str(typed.sessions.timezone),
        "session_windows": sorted(str(name) for name in typed.sessions.windows),
        "feature_windows": {
            str(name): int(value) for name, value in typed.features.windows.items()
        },
        "forward_horizons": [int(value) for value in typed.features.forward_horizons],
        "allowed_forward_columns": [
            str(value) for value in typed.features.allowed_forward_columns
        ],
        "statistics": {
            "seed": int(typed.statistics.seed),
            "bootstrap_samples": int(typed.statistics.bootstrap_samples),
            "permutation_samples": int(typed.statistics.permutation_samples),
            "null_samples": int(typed.statistics.null_samples),
            "block_size": int(typed.statistics.block_size),
            "correction": typed.statistics.correction,
        },
        "market_structure": {
            "enable_quality": bool(typed.market_structure.enable_quality),
            "quality_windows": [
                int(value) for value in typed.market_structure.quality_windows
            ],
            "calibration_candidates": int(
                typed.market_structure.calibration_candidates
            ),
            "validation_horizon": int(typed.market_structure.validation_horizon),
        },
        "modeling": {
            "feature_columns": [str(value) for value in typed.modeling.feature_columns],
            "pca_components": int(typed.modeling.pca_components),
            "clusters": int(typed.modeling.clusters),
            "minimum_samples": int(typed.modeling.minimum_samples),
            "seed": int(typed.modeling.seed),
        },
        "studies": {
            "continue_on_study_error": bool(typed.studies.continue_on_study_error),
        },
    }


__all__ = (
    "APPROVED_OVERRIDE_KEYS",
    "REQUIRED_STAGES",
    "RESEARCH_STAGES",
    "PresetError",
    "build_preset_config",
    "describe_effective_configuration",
    "get_artifact_root",
    "get_stage_vocabulary",
    "list_research_presets",
    "resolve_selected_stages",
)
