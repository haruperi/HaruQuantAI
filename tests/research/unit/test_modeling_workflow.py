"""Unit tests for Research unsupervised workflow (FR-RES-088)."""

import pandas as pd
import pytest
from app.composition.logging import get_logger
from app.services.research import (
    create_research_value,
    run_unsupervised_research,
)

logger = get_logger(__name__)


def _config() -> object:
    """Build a modeling configuration."""
    return create_research_value(
        "UnsupervisedResearchConfig", ("a", "b"), True, 2, 2, 20, 7
    )


def _features(rows: int = 25) -> pd.DataFrame:
    """Build a finite numeric feature frame."""
    return pd.DataFrame({"a": range(rows), "b": [i * 2 for i in range(rows)]})


def test_workflow_is_stateless_seeded_and_advisory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-RES-088: unit composition is seeded and advisory-only.

    Real PCA and K-Means collaboration is exercised by the integration suite.
    """
    logger.debug("Testing Research unsupervised workflow")
    monkeypatch.setattr(
        "app.services.research.modeling.workflow.cluster_feature_space",
        lambda _features, *, config: {
            "labels": [0] * len(_features),
            "seed": config.seed,
        },
    )
    monkeypatch.setattr(
        "app.services.research.modeling.workflow.build_unsupervised_insight_report",
        lambda _features, *, config: {
            "descriptive": {"rows": len(_features)},
            "pca": {"components": config.pca_components},
        },
    )
    result = run_unsupervised_research(
        _features(),
        config=_config(),
        limits=create_research_value(
            "ResearchResourceLimits", 500_000, 600.0, 52_428_800
        ),
    )
    assert result.schema_version == "v1"
    assert result.seed == 7
    assert result.advisory_only is True


def test_workflow_resource_and_evidence_guards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cover row bounds, sample bounds, malformed insight, and empty PCA warning."""
    with pytest.raises(ValueError, match="ROW_LIMIT_EXCEEDED"):
        run_unsupervised_research(
            _features(),
            config=_config(),
            limits=create_research_value("ResearchResourceLimits", 5, 10.0, 1_024),
        )
    with pytest.raises(ValueError, match="INSUFFICIENT_MODELING_SAMPLES"):
        run_unsupervised_research(
            _features(2),
            config=_config(),
            limits=create_research_value("ResearchResourceLimits", 100, 10.0, 1_024),
        )
    monkeypatch.setattr(
        "app.services.research.modeling.workflow.cluster_feature_space",
        lambda _features, *, config: {"labels": []},
    )
    monkeypatch.setattr(
        "app.services.research.modeling.workflow.build_unsupervised_insight_report",
        lambda _features, *, config: {
            "descriptive": "bad",
            "pca": {},
        },
    )
    with pytest.raises(ValueError, match="INVALID_INSIGHT_REPORT"):
        run_unsupervised_research(
            _features(),
            config=_config(),
            limits=create_research_value("ResearchResourceLimits", 100, 10.0, 1_024),
        )
    monkeypatch.setattr(
        "app.services.research.modeling.workflow.build_unsupervised_insight_report",
        lambda _features, *, config: {
            "descriptive": {"rows": 25},
            "pca": {},
        },
    )
    result = run_unsupervised_research(
        _features(),
        config=_config(),
        limits=create_research_value("ResearchResourceLimits", 100, 10.0, 1_024),
    )
    assert result.warnings[0].code == "EMPTY_PCA"
