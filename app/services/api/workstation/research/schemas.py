"""Research gateway request schemas."""

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import time
from pathlib import Path
from types import MappingProxyType
from typing import cast

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from app.services.data import build_market_dataset, is_market_dataset
from app.services.research import create_research_value, is_research_value
from app.utils import get_logger

logger = get_logger(__name__)


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


__all__ = ("ResearchRunRequest",)
