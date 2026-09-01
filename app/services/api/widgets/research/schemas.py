"""Research gateway request schemas.

Two generations of contract live here. `ResearchRunRequest` is the original
synchronous boundary that accepts already-serialized owner contracts. Every
other contract is browser-safe: a caller names an instrument, a window, a
preset, and a bounded override set, and the gateway resolves the canonical
dataset, artifact root, and resource ceilings itself.
"""

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import datetime, time
from pathlib import Path
from types import MappingProxyType
from typing import Literal, Self, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from app.composition.logging import get_logger
from app.services.api.contracts.models import _BaseApiContract, _validate_non_empty
from app.services.data import build_market_dataset, is_market_dataset
from app.services.research import create_research_value, is_research_value

logger = get_logger(__name__)

_MAX_TAGS = 12
_MAX_TAG_LENGTH = 40
_MAX_STAGES = 16
_MAX_STAGE_LENGTH = 40
_MAX_OVERRIDES = 24
_MAX_BAR_LIMIT = 200_000
_MAX_BATCH_SYMBOLS = 25
_MAX_SYMBOL_LENGTH = 64
_MIN_COMPARISON_RUNS = 2
_MAX_COMPARISON_RUNS = 5

ResearchTimeframe = Literal["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"]


def _serialize_mappingproxy(value: object) -> object:
    """Recursively convert mapping proxies, tuples, and dataclasses to JSON-safe values.

    Returns:
        The validated, bounded result.
    """
    if is_dataclass(value):
        return {
            field.name: _serialize_mappingproxy(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, MappingProxyType):
        return {key: _serialize_mappingproxy(item) for key, item in value.items()}
    if isinstance(value, Mapping):
        return {key: _serialize_mappingproxy(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_serialize_mappingproxy(item) for item in value]
    return value


def _coerce_time(value: str | time) -> time:
    """Normalize one session boundary value.

    Returns:
        The validated, bounded result.
    """
    if isinstance(value, time):
        return value
    return time.fromisoformat(value)


class ResearchRunRequest(BaseModel):
    """Bounded authenticated request for one advisory Research run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    hypothesis: str
    dataset: object
    config: object

    @field_validator("hypothesis")
    @classmethod
    def _validate_hypothesis(cls, value: str) -> str:
        """Validate explicit researcher-supplied hypothesis text.

        Returns:
            The validated, bounded result.

        Raises:
            ValueError: If the declared validation fails.
        """
        logger.debug("Validating API Research hypothesis")
        if not value or value != value.strip():
            raise ValueError("hypothesis must be non-empty and trimmed")
        return value

    @field_validator("dataset", mode="before")
    @classmethod
    def _coerce_dataset(cls, value: object) -> object:
        """Validate or rebuild one Data dataset contract.

        Returns:
            The validated, bounded result.

        Raises:
            TypeError: If the declared validation fails.
        """
        if is_market_dataset(value):
            return value
        if not isinstance(value, Mapping):
            raise TypeError("dataset must be a MarketDataset or serialized mapping")
        return build_market_dataset(**value)

    @field_validator("config", mode="before")
    @classmethod
    def _coerce_config(cls, value: object) -> object:
        """Accept either domain objects or serialized JSON payloads.

        Returns:
            The validated, bounded result.

        Raises:
            TypeError: If the declared validation fails.
        """
        if is_research_value(value, "EdgeLabConfig"):
            return value
        if not isinstance(value, Mapping):
            raise TypeError("config must be EdgeLabConfig or serialized mapping")

        sessions = cast("Mapping[str, object]", value["sessions"])
        windows = cast("Mapping[str, tuple[object, object]]", sessions["windows"])

        return create_research_value(
            "EdgeLabConfig",
            cleaning=create_research_value(
                "CleaningConfig", **cast("Mapping[str, object]", value["cleaning"])
            ),
            enrichment=create_research_value(
                "EnrichmentConfig", **cast("Mapping[str, object]", value["enrichment"])
            ),
            features=create_research_value(
                "FeatureConfig", **cast("Mapping[str, object]", value["features"])
            ),
            statistics=create_research_value(
                "StatisticalConfig", **cast("Mapping[str, object]", value["statistics"])
            ),
            studies=create_research_value(
                "StudyConfig", **cast("Mapping[str, object]", value["studies"])
            ),
            sessions=create_research_value(
                "SessionConfig",
                timezone=cast("str", sessions["timezone"]),
                windows={
                    key: (
                        _coerce_time(cast("str | time", windows[key][0])),
                        _coerce_time(cast("str | time", windows[key][1])),
                    )
                    for key in windows
                },
                overlap_precedence=tuple(
                    cast("tuple[str, ...] | list[str]", sessions["overlap_precedence"])
                ),
            ),
            market_structure=create_research_value(
                "MarketStructureConfig",
                **cast("Mapping[str, object]", value["market_structure"]),
            ),
            modeling=create_research_value(
                "UnsupervisedResearchConfig",
                **cast("Mapping[str, object]", value["modeling"]),
            ),
            artifacts=create_research_value(
                "ArtifactWriteConfig",
                allowed_root=Path(str(value["artifacts"]["allowed_root"])),
                **{
                    key: value["artifacts"][key]
                    for key in value["artifacts"]
                    if key != "allowed_root"
                },
            ),
            limits=create_research_value(
                "ResearchResourceLimits",
                **cast("Mapping[str, object]", value["limits"]),
            ),
            selected_stages=tuple(
                cast("tuple[str, ...] | list[str]", value["selected_stages"])
            ),
        )

    @field_serializer("config", when_used="json")
    def _serialize_config(self, value: object) -> dict[str, object]:
        """Serialize configuration with mappingproxy-safe nested values.

        Returns:
            The validated, bounded result.
        """
        return cast("dict[str, object]", _serialize_mappingproxy(value))


class ResearchExperimentCreateRequest(_BaseApiContract):
    """Bounded request creating one research experiment ledger entry."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.research_experiment_create_request.v1"] = (
        "api.research_experiment_create_request.v1"
    )
    name: str = Field(min_length=1, max_length=120)
    hypothesis: str = Field(min_length=1, max_length=1_000)
    notes: str | None = Field(default=None, max_length=4_000)
    tags: tuple[str, ...] = ()

    @field_validator("name", "hypothesis")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one trimmed non-empty experiment field.

        Returns:
            The validated, bounded result.
        """
        return _validate_non_empty(value, "field")

    @field_validator("tags")
    @classmethod
    def _validate_tags(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate a bounded set of trimmed tags.

        Returns:
            The validated, bounded result.

        Raises:
            ValueError: If the tag list or any tag exceeds its bound.
        """
        if len(value) > _MAX_TAGS:
            message = f"at most {_MAX_TAGS} tags are accepted"
            raise ValueError(message)
        for tag in value:
            if not tag.strip() or len(tag) > _MAX_TAG_LENGTH:
                raise ValueError("tags must be bounded and non-empty")
        return value


class ResearchDatasetSelection(_BaseApiContract):
    """Safe browser-side description of the dataset a run should analyze.

    A caller names the instrument and window. The server resolves the canonical
    ``MarketDataset`` through Data, so market rows never travel through a
    browser request body.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.research_dataset_selection.v1"] = (
        "api.research_dataset_selection.v1"
    )
    symbol: str = Field(min_length=1, max_length=_MAX_SYMBOL_LENGTH)
    timeframe: ResearchTimeframe = "H1"
    source_id: str | None = Field(default=None, max_length=64)
    start: datetime | None = None
    end: datetime | None = None
    bar_limit: int = Field(default=5_000, gt=0, le=_MAX_BAR_LIMIT)
    asset_class: str | None = Field(default=None, max_length=32)

    @field_validator("symbol")
    @classmethod
    def _validate_symbol(cls, value: str) -> str:
        """Validate one trimmed non-empty instrument symbol.

        Returns:
            The validated, bounded result.
        """
        return _validate_non_empty(value, "symbol")

    @model_validator(mode="after")
    def _validate_window(self) -> Self:
        """Require a forward-ordered window when both bounds are supplied.

        Returns:
            The validated request.

        Raises:
            ValueError: If the window is inverted.
        """
        if self.start is not None and self.end is not None and self.start >= self.end:
            raise ValueError("start must be earlier than end")
        return self


class ResearchRunCreateRequest(_BaseApiContract):
    """Bounded safe request starting one background Research run.

    The gateway resolves the canonical dataset, artifact root, resource limits,
    session policy, and effective preset. None of those cross the browser
    boundary.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.research_run_create_request.v1"] = (
        "api.research_run_create_request.v1"
    )
    dataset: ResearchDatasetSelection
    dataset_id: str | None = Field(default=None, max_length=200)
    preset: str = Field(default="standard_edge", min_length=1, max_length=64)
    selected_stages: tuple[str, ...] = ()
    approved_overrides: Mapping[str, object] = Field(default_factory=dict)
    seed: int | None = Field(default=None, ge=0)
    performance_report_id: str | None = Field(default=None, max_length=200)
    reason: str | None = Field(default=None, max_length=500)
    force_rerun: bool = False
    save_artifacts: bool = True
    hypothesis: str | None = Field(default=None, max_length=1_000)

    @field_validator("selected_stages")
    @classmethod
    def _validate_stages(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate a bounded stage selection.

        Returns:
            The validated, bounded result.

        Raises:
            ValueError: If the selection or a stage name exceeds its bound.
        """
        if len(value) > _MAX_STAGES:
            raise ValueError("too many selected stages")
        for stage in value:
            if not stage.strip() or len(stage) > _MAX_STAGE_LENGTH:
                raise ValueError("stage names must be bounded and non-empty")
        return value

    @field_validator("approved_overrides")
    @classmethod
    def _validate_overrides(cls, value: Mapping[str, object]) -> Mapping[str, object]:
        """Validate a bounded approved-override mapping.

        Returns:
            The validated, bounded result.

        Raises:
            ValueError: If the mapping exceeds its bound.
        """
        if len(value) > _MAX_OVERRIDES:
            message = f"at most {_MAX_OVERRIDES} overrides are accepted"
            raise ValueError(message)
        return value


class ResearchComparisonRequest(_BaseApiContract):
    """Bounded request comparing two or more completed Research runs."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.research_comparison_request.v1"] = (
        "api.research_comparison_request.v1"
    )
    run_ids: tuple[str, ...]

    @field_validator("run_ids")
    @classmethod
    def _validate_run_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate a bounded distinct comparison selection.

        Returns:
            The validated, bounded result.

        Raises:
            ValueError: If the selection is outside bounds or duplicated.
        """
        if not _MIN_COMPARISON_RUNS <= len(value) <= _MAX_COMPARISON_RUNS:
            raise ValueError("between two and five runs may be compared")
        if len(set(value)) != len(value):
            raise ValueError("run identifiers must be distinct")
        return value


class ResearchAutomationRequest(_BaseApiContract):
    """Bounded request queueing one multi-symbol Research batch."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.research_automation_request.v1"] = (
        "api.research_automation_request.v1"
    )
    experiment_id: str = Field(min_length=1, max_length=200)
    symbols: tuple[str, ...]
    timeframe: ResearchTimeframe = "H1"
    source_id: str | None = Field(default=None, max_length=64)
    start: datetime | None = None
    end: datetime | None = None
    bar_limit: int = Field(default=5_000, gt=0, le=_MAX_BAR_LIMIT)
    preset: str = Field(default="standard_edge", min_length=1, max_length=64)
    selected_stages: tuple[str, ...] = ()
    approved_overrides: Mapping[str, object] = Field(default_factory=dict)
    use_cache: bool = True
    force_rerun: bool = False
    save_artifacts: bool = True
    trigger: Literal["manual", "scheduled"] = "manual"
    reason: str | None = Field(default=None, max_length=500)

    @field_validator("symbols")
    @classmethod
    def _validate_symbols(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate a bounded distinct symbol universe.

        Returns:
            The validated, bounded result.

        Raises:
            ValueError: If the universe is empty, oversized, or duplicated.
        """
        if not 0 < len(value) <= _MAX_BATCH_SYMBOLS:
            message = f"between one and {_MAX_BATCH_SYMBOLS} symbols are accepted"
            raise ValueError(message)
        for symbol in value:
            if not symbol.strip() or len(symbol) > _MAX_SYMBOL_LENGTH:
                raise ValueError("symbols must be bounded and non-empty")
        if len({symbol.strip().upper() for symbol in value}) != len(value):
            raise ValueError("symbols must be distinct")
        return value


class ResearchExpectancyTransitionRequest(_BaseApiContract):
    """Governed request advancing one expectancy profile lifecycle."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.research_expectancy_transition_request.v1"] = (
        "api.research_expectancy_transition_request.v1"
    )
    target_state: Literal[
        "draft", "under_review", "approved", "suspended", "expired", "revoked"
    ]
    decision: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=500)
    superseded_by: str | None = Field(default=None, min_length=1, max_length=200)


class ResearchExpectancyCreateRequest(_BaseApiContract):
    """Governed request creating a draft profile from completed-run evidence."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.research_expectancy_create_request.v1"] = (
        "api.research_expectancy_create_request.v1"
    )
    run_id: str = Field(min_length=1, max_length=200)
    exact_version: str = Field(min_length=1, max_length=100)
    strategy_ref: str = Field(min_length=1, max_length=200)
    regimes: tuple[str, ...] = Field(default_factory=tuple, max_length=32)
    sessions: tuple[str, ...] = Field(default_factory=tuple, max_length=32)
    sample_from_utc: datetime
    sample_to_utc: datetime
    sample_size: int = Field(gt=0)
    out_of_sample_status: Literal["in_sample", "out_of_sample", "walk_forward"]
    win_rate: float = Field(ge=0.0, le=1.0)
    avg_win_r: float = Field(ge=0.0)
    avg_loss_r: float = Field(ge=0.0)
    expected_value_r: float
    max_drawdown_r: float = Field(ge=0.0)
    min_reward_risk: float = Field(ge=0.0)
    next_review_at_utc: datetime | None = None
    expires_at_utc: datetime | None = None


class ResearchStressScenarioCreateRequest(_BaseApiContract):
    """Governed request instantiating one approved stress scenario."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.research_stress_scenario_create_request.v1"] = (
        "api.research_stress_scenario_create_request.v1"
    )
    scenario_key: Literal[
        "broad_market_dislocation",
        "severe_fx_repricing",
        "liquidity_withdrawal",
        "venue_connectivity_disruption",
        "extreme_combined_tail",
    ]
    hypothesis: str = Field(min_length=1, max_length=500)


__all__ = (
    "ResearchAutomationRequest",
    "ResearchComparisonRequest",
    "ResearchDatasetSelection",
    "ResearchExpectancyCreateRequest",
    "ResearchExpectancyTransitionRequest",
    "ResearchExperimentCreateRequest",
    "ResearchRunCreateRequest",
    "ResearchRunRequest",
    "ResearchStressScenarioCreateRequest",
    "ResearchTimeframe",
)
