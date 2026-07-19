"""Unit tests for canonical Research feature-frame assembly."""

import pandas as pd
from app.services.indicators import sma
from app.services.research.contracts import (
    DataQualityReport,
    FeatureConfig,
    PreparedDataset,
    ResearchResourceLimits,
)
from app.services.research.features import build_research_feature_frame
from app.utils import logger
from tests.indicators.helpers import build_dataset

_HASH = "c" * 64


def test_feature_frame_records_lineage_and_forward_columns() -> None:
    """Verify shared indicator lineage and forward exclusions are explicit."""
    logger.debug("Testing Research feature-frame lineage")
    dataset = build_dataset(
        [
            (price, price + 1, price - 1, price, 100.0)
            for price in (100 + index + (index % 3) * 0.2 for index in range(30))
        ]
    )
    index = pd.DatetimeIndex([record.timestamp for record in dataset.records], tz="UTC")
    frame = pd.DataFrame(
        {
            "open": [float(record.open) for record in dataset.records],
            "high": [float(record.high) for record in dataset.records],
            "low": [float(record.low) for record in dataset.records],
            "close": [float(record.close) for record in dataset.records],
            "volume": [float(record.volume) for record in dataset.records],
            "spread": [0.0] * len(dataset.records),
        },
        index=index,
    )
    prepared = PreparedDataset(
        frame,
        "v1",
        DataQualityReport((), (), ("schema",), ()),
        _HASH,
        _HASH,
        ("fixture",),
    )
    original = prepared.data.copy(deep=True)
    features, metadata = build_research_feature_frame(
        prepared,
        indicator_results={"sma": sma(dataset, period=5)},
        config=FeatureConfig({"hurst": 20}, (2,), ("forward_return_2",), "preserve"),
        limits=ResearchResourceLimits(100, 10.0, 1024),
    )
    assert "sma_5" in features
    assert "forward_return_2" not in metadata["training_feature_columns"]
    assert metadata["indicator_lineage"]
    assert prepared.data.equals(original)
