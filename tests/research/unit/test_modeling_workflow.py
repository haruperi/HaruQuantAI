"""Unit tests for Research unsupervised workflow (FR-RES-088)."""

import pandas as pd
from app.services.research import (
    ResearchResourceLimits,
    UnsupervisedResearchConfig,
)
from app.services.research.modeling import run_unsupervised_research
from app.utils import logger


def _config() -> UnsupervisedResearchConfig:
    """Build a modeling configuration."""
    return UnsupervisedResearchConfig(("a", "b"), True, 2, 2, 20, 7)


def _features(rows: int = 25) -> pd.DataFrame:
    """Build a finite numeric feature frame."""
    return pd.DataFrame({"a": range(rows), "b": [i * 2 for i in range(rows)]})


def test_workflow_is_stateless_seeded_and_advisory() -> None:
    """FR-RES-088: workflow is stateless, seeded, and advisory-only."""
    logger.debug("Testing Research unsupervised workflow")
    result = run_unsupervised_research(
        _features(),
        config=_config(),
        limits=ResearchResourceLimits(500_000, 600.0, 52_428_800),
    )
    assert result.schema_version == "v1"
    assert result.seed == 7
    assert result.advisory_only is True
