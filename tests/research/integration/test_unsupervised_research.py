"""Integration evidence for WF-RES-008: unsupervised workflow."""

import pandas as pd
from app.services.research import (
    ResearchResourceLimits,
    UnsupervisedResearchConfig,
    UnsupervisedResearchResult,
)
from app.services.research.modeling import run_unsupervised_research
from app.utils import logger


def test_unsupervised_workflow_is_seeded_and_advisory() -> None:
    """WF-RES-008: workflow is seeded, advisory, and reproducible."""
    logger.debug("Testing Research unsupervised workflow integration")
    features = pd.DataFrame({"a": range(25), "b": [i * 2 for i in range(25)]})
    config = UnsupervisedResearchConfig(("a", "b"), True, 2, 2, 20, 7)
    result = run_unsupervised_research(
        features,
        config=config,
        limits=ResearchResourceLimits(500_000, 600.0, 52_428_800),
    )
    assert isinstance(result, UnsupervisedResearchResult)
    assert result.seed == 7
    assert result.advisory_only is True
