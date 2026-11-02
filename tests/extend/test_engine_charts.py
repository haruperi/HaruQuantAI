"""Unit tests for EngineCharts cohort and telemetry series projection."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.extend.engine_charts import (
    CHART_CLASSES,
    COLOR_BLUE,
    COLOR_GREEN,
    DATA_TYPE_CHART,
    DATA_TYPE_GRID,
    DATA_TYPE_ROWS,
    ENGINE_CHARTS,
    MEGABYTE,
    TYPE_GLOBAL,
    TYPE_PROJECT_BASED,
    AcceptedStrategiesPerHour,
    AverageStrategiesPerHourChart,
    Databank,
    DatabankFitnessIS,
    DatabankFitnessIST,
    DatabankFitnessISV,
    DatabankFitnessOOS,
    EngineChart,
    EngineChartDescriptor,
    EngineChartsCatalog,
    FitnessCollectionData,
    GeneticEvolutionInfo,
    GeneticInfo,
    GenEvoFitnessIS,
    GenEvoFitnessIST,
    GenEvoFitnessISV,
    GenEvoFitnessOOS,
    GPFitnessEvolutionData,
    HeapMemoryChart,
    HeapMemoryUsage,
    JobRuntimeTelemetrySnapshot,
    MemoryBean,
    MemoryInfo,
    OffHeapMemoryChart,
    OffHeapMemoryInfoChart,
    Project,
    ProjectRunInfo,
    TimeSeries,
    TimeSeriesAreaChart,
    TimeSeriesLineChart,
    format_bytes_to_human_format,
)


class TestEngineChartsCatalog:
    """Test suite for EngineCharts catalog, descriptors, and telemetry projection."""

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

    def test_chart_classes_mapping(self) -> None:
        """Verify all 14 chart IDs map to valid EngineChart subclasses."""
        assert len(CHART_CLASSES) == 14
        classes = EngineChartsCatalog.list_classes()
        assert len(classes) == 14
        for chart_id, cls in classes.items():
            assert issubclass(cls, EngineChart)
            assert EngineChartsCatalog.get_class(chart_id) is cls

        with pytest.raises(DomainError) as exc_info:
            EngineChartsCatalog.get_class("UnknownClass")
        assert exc_info.value.code == "ENGINE_CHART_NOT_FOUND"

    def test_create_chart_factory(self) -> None:
        """Verify create_chart factory returns working chart instances."""
        for chart_id in CHART_CLASSES:
            chart = EngineChartsCatalog.create_chart(chart_id)
            assert isinstance(chart, EngineChart)
            assert isinstance(chart.name, str)

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


class TestTimeSeriesAndFormatting:
    """Test suite for TimeSeries primitives and byte formatting utility."""

    def test_format_bytes_to_human_format(self) -> None:
        """Verify byte counts convert to expected human strings."""
        assert format_bytes_to_human_format(-10) == "0 B"
        assert format_bytes_to_human_format(0) == "0 B"
        assert format_bytes_to_human_format(500) == "500 B"
        assert format_bytes_to_human_format(1024) == "1.0 KB"
        assert format_bytes_to_human_format(1024 * 1024) == "1.0 MB"
        assert format_bytes_to_human_format(int(2.5 * 1024 * 1024 * 1024)) == "2.5 GB"

    def test_time_series_points_and_trimming(self) -> None:
        """Verify TimeSeries capacity constraint and point management."""
        ts = TimeSeries(name="TestSeries", points_count=3, color=COLOR_GREEN)
        ts.add_value(1000, 10.0)
        ts.addValue(2000, 20.0)
        ts.add_value(3000, 30.0)
        assert len(ts.points) == 3

        # Add 4th point: first point should be evicted
        ts.add_value(4000, 40.0)
        assert len(ts.points) == 3
        assert ts.points[0].timestamp_ms == 2000
        assert ts.points[-1].value == 40.0

        data = ts.to_json()
        assert data["name"] == "TestSeries"
        assert data["color"] == COLOR_GREEN
        assert len(data["points"]) == 3
        assert ts.toJSON() == data

        ts.clear()
        assert len(ts.points) == 0

    def test_time_series_charts_config(self) -> None:
        """Verify line and area charts configuration and JSON serialization."""
        line_chart = TimeSeriesLineChart()
        line_chart.xAxisTitle = "Time"
        line_chart.yAxisTitle = "Rate"
        line_chart.yAxisRangeMin = 0.0
        line_chart.yAxisRangeMax = 100.0
        line_chart.maxXTicksLimit = 5
        line_chart.maxYTicksLimit = 8
        line_chart.showLegend = True
        line_chart.yAxisTicksMemory = False

        s = TimeSeries("S1", color=COLOR_BLUE)
        line_chart.addSeries(s)
        payload = line_chart.toJSON()

        assert payload["chartType"] == "line"
        assert payload["xAxisTitle"] == "Time"
        assert payload["yAxisTitle"] == "Rate"
        assert payload["yAxisRangeMin"] == 0.0
        assert payload["yAxisRangeMax"] == 100.0
        assert payload["maxXTicksLimit"] == 5
        assert payload["maxYTicksLimit"] == 8
        assert payload["showLegend"] is True
        assert len(payload["series"]) == 1

        area_chart = TimeSeriesAreaChart()
        assert area_chart.chart_type == "area"


class TestThroughputEngineCharts:
    """Test suite for AcceptedStrategiesPerHour and AverageStrategiesPerHourChart."""

    def test_accepted_strategies_per_hour(self) -> None:
        """Verify AcceptedStrategiesPerHour sampling and refresh throttling."""
        run_info = ProjectRunInfo(
            total_jobs_done=10,
            accepted_strategies_per_hour=42.5,
            strategies_per_hour=100.0,
        )
        project = Project(is_running=True, run_info=run_info)
        chart = AcceptedStrategiesPerHour(project=project)

        assert chart.chart_type == TYPE_PROJECT_BASED
        assert chart.name == "Accepted strategies per hour"

        # Sampling while running
        chart.add_next_value()
        assert len(chart.series.points) == 1
        assert chart.series.points[0].value == 42.5

        # Print initial change
        p1 = chart.print()
        assert p1 is not None
        assert p1["type"] == DATA_TYPE_CHART

        # Print without change returns None
        p2 = chart.print()
        assert p2 is None

        # Print after 10 checks with no change triggers refresh on the 10th check (when checks > 10)
        refresh_results = [chart.print() for _ in range(10)]
        assert any(r is not None for r in refresh_results)

        # Sampling when stopped does nothing
        stopped_project = Project(is_running=False, run_info=run_info)
        chart_stopped = AcceptedStrategiesPerHour(project=stopped_project)
        chart_stopped.add_next_value()
        assert len(chart_stopped.series.points) == 0

    def test_average_strategies_per_hour_chart(self) -> None:
        """Verify AverageStrategiesPerHourChart sampling and print logic."""
        run_info = ProjectRunInfo(
            total_jobs_done=5,
            accepted_strategies_per_hour=10.0,
            strategies_per_hour=250.0,
        )
        project = Project(is_running=True, run_info=run_info)
        chart = AverageStrategiesPerHourChart(project=project)

        assert chart.chart_type == TYPE_PROJECT_BASED
        assert chart.name == "Average strategies per hour"

        chart.add_next_value()
        assert len(chart.series.points) == 1
        assert chart.series.points[0].value == 250.0

        p1 = chart.print()
        assert p1 is not None
        assert p1["type"] == DATA_TYPE_CHART


class TestDatabankFitnessEngineCharts:
    """Test suite for DatabankFitness (IS, IST, ISV, OOS) engine charts."""

    def test_databank_fitness_is(self) -> None:
        """Verify DatabankFitnessIS sampling, series values, and reset."""
        fit_data = FitnessCollectionData(
            best_fitness_is=0.95,
            top_avg_fitness_is=0.88,
            avg_fitness_is=0.65,
        )
        databank = Databank(fitness_data=fit_data)
        project = Project(is_running=True, databank=databank)
        chart = DatabankFitnessIS(project=project)

        assert chart.name == "Databank Fitness - IS"
        chart.add_next_value()

        assert len(chart.best_series.points) == 1
        assert chart.best_series.points[0].value == 0.95
        assert chart.top_avg_series.points[0].value == 0.88
        assert chart.avg_series.points[0].value == 0.65

        p = chart.print()
        assert p is not None
        assert p["type"] == DATA_TYPE_CHART
        assert len(p["chart"]["series"]) == 3

        chart.reset()
        assert len(chart.best_series.points) == 0

    def test_databank_fitness_ist_isv_oos(self) -> None:
        """Verify DatabankFitnessIST, ISV, and OOS metric extraction."""
        fit_data = FitnessCollectionData(
            best_fitness_ist=0.91,
            top_avg_fitness_ist=0.82,
            avg_fitness_ist=0.55,
            best_fitness_isv=0.87,
            top_avg_fitness_isv=0.79,
            avg_fitness_isv=0.51,
            best_fitness_oos=0.83,
            top_avg_fitness_oos=0.74,
            avg_fitness_oos=0.48,
        )
        databank = Databank(fitness_data=fit_data)
        project = Project(is_running=True, databank=databank)

        c_ist = DatabankFitnessIST(project=project)
        c_ist.add_next_value()
        assert c_ist.best_series.points[0].value == 0.91
        assert c_ist.print() is not None
        c_ist.reset()
        assert len(c_ist.best_series.points) == 0

        c_isv = DatabankFitnessISV(project=project)
        c_isv.add_next_value()
        assert c_isv.best_series.points[0].value == 0.87
        assert c_isv.print() is not None
        c_isv.reset()
        assert len(c_isv.best_series.points) == 0

        c_oos = DatabankFitnessOOS(project=project)
        c_oos.add_next_value()
        assert c_oos.best_series.points[0].value == 0.83
        assert c_oos.print() is not None
        c_oos.reset()
        assert len(c_oos.best_series.points) == 0

        # Test project stopped
        stopped = Project(is_running=False, databank=databank)
        c_stopped = DatabankFitnessIS(project=stopped)
        c_stopped.add_next_value()
        assert len(c_stopped.best_series.points) == 0


class TestGeneticEvolutionEngineCharts:
    """Test suite for GeneticEvolutionInfo and GenEvoFitness (IS/IST/ISV/OOS)."""

    def test_genetic_evolution_info_no_data(self) -> None:
        """Verify GeneticEvolutionInfo when genetic evolution is inactive."""
        project = Project(genetic_info=GeneticInfo(is_genetic=False))
        chart = GeneticEvolutionInfo(project=project)
        chart.add_next_value()  # no-op check

        payload = chart.print()
        assert payload is not None
        assert payload["type"] == DATA_TYPE_ROWS
        assert payload["items"] == [
            {"name": "No data", "value": "No genetic evolution running"}
        ]

    def test_genetic_evolution_info_active_islands(self) -> None:
        """Verify GeneticEvolutionInfo renders rows for active islands."""
        islands = [
            GPFitnessEvolutionData(generation=3, population_size=100),
            GPFitnessEvolutionData(generation=4, population_size=120),
        ]
        project = Project(
            genetic_info=GeneticInfo(is_genetic=True, islands_evo_data=islands)
        )
        chart = GeneticEvolutionInfo(project=project)

        payload = chart.print()
        assert payload is not None
        assert payload["type"] == DATA_TYPE_ROWS
        assert len(payload["items"]) == 2
        assert payload["items"][0]["name"] == "Island #1"
        assert "Generation: 3" in payload["items"][0]["value"]
        assert "Population: 100" in payload["items"][0]["value"]

    def test_gen_evo_fitness_is_ist_isv_oos(self) -> None:
        """Verify Island #1 genetic fitness curves across IS, IST, ISV, and OOS."""
        gen_data = FitnessCollectionData(
            best_fitness_is=0.92,
            top_avg_fitness_is=0.81,
            avg_fitness_is=0.60,
            best_fitness_ist=0.90,
            top_avg_fitness_ist=0.78,
            avg_fitness_ist=0.58,
            best_fitness_isv=0.85,
            top_avg_fitness_isv=0.75,
            avg_fitness_isv=0.52,
            best_fitness_oos=0.80,
            top_avg_fitness_oos=0.70,
            avg_fitness_oos=0.45,
        )
        island = GPFitnessEvolutionData(generation=0, generation_data=[gen_data])
        gen_info = GeneticInfo(is_genetic=True, islands_evo_data=[island])
        project = Project(is_running=True, genetic_info=gen_info)

        c_is = GenEvoFitnessIS(project=project)
        c_is.add_next_value()
        assert c_is.best_series.points[0].value == 0.92
        assert c_is.best5_avg_series.points[0].value == 0.81
        assert c_is.avg_series.points[0].value == 0.60

        c_ist = GenEvoFitnessIST(project=project)
        c_ist.add_next_value()
        assert c_ist.best_series.points[0].value == 0.90
        assert c_ist.print() is not None
        c_ist.reset()
        assert len(c_ist.best_series.points) == 0

        c_isv = GenEvoFitnessISV(project=project)
        c_isv.add_next_value()
        assert c_isv.best_series.points[0].value == 0.85
        assert c_isv.print() is not None
        c_isv.reset()
        assert len(c_isv.best_series.points) == 0

        c_oos = GenEvoFitnessOOS(project=project)
        c_oos.add_next_value()
        assert c_oos.best_series.points[0].value == 0.80
        assert c_oos.print() is not None
        c_oos.reset()
        assert len(c_oos.best_series.points) == 0

        c_is.reset()
        assert len(c_is.best_series.points) == 0


class TestMemoryEngineCharts:
    """Test suite for HeapMemoryChart, OffHeapMemoryChart, and OffHeapMemoryInfoChart."""

    def test_heap_memory_chart(self) -> None:
        """Verify HeapMemoryChart sampling and memory area chart rendering."""
        heap_usage = HeapMemoryUsage(
            used=256 * MEGABYTE,
            committed=512 * MEGABYTE,
            max_bytes=1024 * MEGABYTE,
        )
        bean = MemoryBean(heap_usage=heap_usage)
        chart = HeapMemoryChart(memory_bean=bean, max_heap_memory=1024 * MEGABYTE)

        assert chart.chart_type == TYPE_GLOBAL
        assert chart.name == "Heap memory chart"

        chart.add_next_value()
        assert len(chart.memory_usage_series.points) == 1
        assert chart.memory_usage_series.points[0].value == 256.0
        assert chart.heap_size_series.points[0].value == 512.0

        p = chart.print()
        assert p is not None
        assert p["type"] == DATA_TYPE_CHART
        assert p["chart"]["chartType"] == "area"

        chart.checks = 5000
        p_gc = chart.print()
        assert p_gc is not None
        assert chart.checks == 5001

    def test_off_heap_memory_chart(self) -> None:
        """Verify OffHeapMemoryChart sampling with non-negative clamping."""
        info = MemoryInfo(allocated_memory=128 * MEGABYTE)
        chart = OffHeapMemoryChart(off_heap_info=info)

        assert chart.chart_type == TYPE_GLOBAL
        assert chart.name == "Off-heap memory chart"

        chart.add_next_value()
        assert len(chart.series.points) == 1
        assert chart.series.points[0].value == 128.0

        p = chart.print()
        assert p is not None
        assert p["type"] == DATA_TYPE_CHART

    def test_off_heap_memory_info_chart(self) -> None:
        """Verify OffHeapMemoryInfoChart grid formatting."""
        info = MemoryInfo(
            allocated_objects=45000,
            allocated_memory=64 * MEGABYTE,
        )
        chart = OffHeapMemoryInfoChart(off_heap_info=info)

        assert chart.chart_type == TYPE_GLOBAL
        assert chart.name == "Off-heap memory info"

        chart.add_next_value()  # no-op check
        p = chart.print()
        assert p is not None
        assert p["type"] == DATA_TYPE_GRID
        assert p["items"][0] == {"name": "Allocated objects", "value": 45000}
        assert p["items"][1] == {"name": "Allocated memory", "value": "64.0 MB"}


class TestDonorCompatibilityModels:
    """Test suite for Java-to-Python property and method compatibility."""

    def test_compatibility_properties(self) -> None:
        """Verify camelCase property aliases for donor compatibility."""
        run_info = ProjectRunInfo()
        run_info.totalJobsDone = 15
        run_info.acceptedStrategiesPerHour = 3.5
        run_info.strategiesPerHour = 100.2
        assert run_info.total_jobs_done == 15
        assert run_info.accepted_strategies_per_hour == 3.5
        assert run_info.strategies_per_hour == 100.2

        fit = FitnessCollectionData(
            best_fitness_is=1.0,
            top_avg_fitness_is=2.0,
            avg_fitness_is=3.0,
            best_fitness_ist=4.0,
            top_avg_fitness_ist=5.0,
            avg_fitness_ist=6.0,
            best_fitness_isv=7.0,
            top_avg_fitness_isv=8.0,
            avg_fitness_isv=9.0,
            best_fitness_oos=10.0,
            top_avg_fitness_oos=11.0,
            avg_fitness_oos=12.0,
        )
        assert fit.bestFitnessIS == 1.0
        assert fit.topAvgFitnessIS == 2.0
        assert fit.avgFitnessIS == 3.0
        assert fit.bestFitnessIST == 4.0
        assert fit.topAvgFitnessIST == 5.0
        assert fit.avgFitnessIST == 6.0
        assert fit.bestFitnessISV == 7.0
        assert fit.topAvgFitnessISV == 8.0
        assert fit.avgFitnessISV == 9.0
        assert fit.bestFitnessOOS == 10.0
        assert fit.topAvgFitnessOOS == 11.0
        assert fit.avgFitnessOOS == 12.0

        mem = MemoryInfo(
            allocated_objects=10,
            allocated_memory=20,
            total_allocated_objects=30,
            total_allocated_memory=40,
        )
        assert mem.allocatedObjects == 10
        assert mem.allocatedMemory == 20
        assert mem.totalAllocatedObjects == 30
        assert mem.totalAllocatedMemory == 40

        h = HeapMemoryUsage(used=100, committed=200, max_bytes=300)
        assert h.getUsed() == 100
        assert h.getCommitted() == 200
        assert h.getMax() == 300

        project = Project(is_running=True)
        assert project.isRunning() is True
        assert project.getResultsDatabank() is not None
        assert isinstance(project.getGeneticInfo(), GeneticInfo)
