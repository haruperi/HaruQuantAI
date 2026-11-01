"""Unit tests for EngineChartsCatalog (EngineCharts cohort)."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.extend.engine_charts import (
    ENGINE_CHARTS,
    EngineChartDescriptor,
    EngineChartsCatalog,
    JobRuntimeTelemetrySnapshot,
)


class TestEngineChartsCatalog:
    """Test suite for EngineCharts catalog and telemetry series projection."""

    def test_registered_charts_count_and_categories(self) -> None:
        """Verify that all 14 donor EngineCharts are registered across 4 categories."""
        assert len(ENGINE_CHARTS) == 14
        descriptors = EngineChartsCatalog.list_descriptors()
        assert len(descriptors) == 14

        categories = {d.category for d in descriptors}
        assert categories == {
            "THROUGHPUT",
            "DATABANK_FITNESS",
            "GENETIC_FITNESS",
            "MEMORY",
        }

    def test_get_and_not_found(self) -> None:
        """Verify get returns descriptor or raises DomainError."""
        desc = EngineChartsCatalog.get("AcceptedStrategiesPerHour")
        assert desc.chart_id == "AcceptedStrategiesPerHour"
        assert desc.category == "THROUGHPUT"

        with pytest.raises(DomainError) as exc_info:
            EngineChartsCatalog.get("UnknownChart")
        assert exc_info.value.code == "ENGINE_CHART_NOT_FOUND"

    def test_project_telemetry_series(self) -> None:
        """Verify projecting telemetry snapshot into series points."""
        telemetry = JobRuntimeTelemetrySnapshot(
            steps=(1, 2, 3),
            timestamps_ms=(1000, 2000, 3000),
            metrics={
                "AcceptedStrategiesPerHour": (120.5, 145.2, 160.0),
                "AcceptedStrategiesPerHour_secondary": (100.0, 110.0, 115.0),
            },
        )

        points = EngineChartsCatalog.project("AcceptedStrategiesPerHour", telemetry)
        assert len(points) == 3
        assert points[0].step == 1
        assert points[0].timestamp_ms == 1000
        assert points[0].value == 120.5
        assert points[0].secondary_value == 100.0

        d = points[0].to_dict()
        assert d["step"] == 1
        assert d["value"] == 120.5

    def test_descriptor_to_dict(self) -> None:
        """Verify EngineChartDescriptor to_dict."""
        desc = EngineChartDescriptor(
            chart_id="C1",
            label="Chart 1",
            category="THROUGHPUT",
            sample_key=None,
            unit="u",
            source_ref="ref",
        )
        d = desc.to_dict()
        assert d["chart_id"] == "C1"
        assert d["category"] == "THROUGHPUT"
