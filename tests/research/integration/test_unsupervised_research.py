"""Integration evidence for WF-RES-008: unsupervised workflow."""

import pandas as pd
from app.services.research import (
    create_research_value,
    is_research_value,
    run_unsupervised_research,
)
from app.utils import get_logger

logger = get_logger(__name__)


def test_unsupervised_workflow_is_seeded_and_advisory() -> None:
    """WF-RES-008: workflow is seeded, advisory, and reproducible."""
    logger.debug("Testing Research unsupervised workflow integration")
    features = pd.DataFrame({"a": range(25), "b": [i * 2 for i in range(25)]})
    config = create_research_value(
        "UnsupervisedResearchConfig", ("a", "b"), True, 2, 2, 20, 7
    )
    result = run_unsupervised_research(
        features,
        config=config,
        limits=create_research_value(
            "ResearchResourceLimits", 500_000, 600.0, 52_428_800
        ),
    )
    assert is_research_value(result, "UnsupervisedResearchResult")
    assert result.seed == 7
    assert result.advisory_only is True
