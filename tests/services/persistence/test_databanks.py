"""Tests for project databanks, ranking, similarity, and views (FEAT-PERSISTENCE-DATABANKS)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from app.contracts.persistence import (
    DATABANK_STORE,
    ArtifactNotFoundError,
    ColumnConfig,
    DatabankNotFoundError,
    DatabankViewConfig,
    DuplicateMemberError,
    RankingDirection,
    SampleType,
    SimilarityProfile,
)
from app.kernel.bootstrapper import Runtime
from app.services.persistence.artifacts import (
    ArtifactConfig,
    ArtifactFeature,
    ArtifactServiceImpl,
)
from app.services.persistence.databanks import (
    DatabankConfig,
    DatabankFeature,
    DatabankServiceImpl,
    feature,
)
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseFeature,
    DatabaseServiceImpl,
)


def _setup_services(
    tmp_path: Path,
) -> tuple[DatabaseServiceImpl, ArtifactServiceImpl, DatabankServiceImpl]:
    """Helper to set up wired persistence services."""
    db_file = tmp_path / "test.db"
    art_dir = tmp_path / "artifacts"
    staging_dir = tmp_path / "staging"

    db = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    art = ArtifactServiceImpl(
        db, ArtifactConfig(artifacts_dir=art_dir, staging_dir=staging_dir)
    )
    dbk = DatabankServiceImpl(db, art)
    return db, art, dbk


def test_databank_crud_and_clear(tmp_path: Path) -> None:
    """Test creating, listing, clearing, and deleting databanks."""
    _db, art, dbk = _setup_services(tmp_path)

    # 1. Create databanks
    d1 = dbk.create_databank("ProjectX", "Results", capacity=500)
    assert d1.project_name == "ProjectX"
    assert d1.databank_name == "Results"
    assert d1.capacity == 500

    d2 = dbk.create_databank("ProjectX", "Archive", capacity=100)
    assert d2.databank_name == "Archive"

    # 2. List databanks
    dbs = dbk.list_databanks("ProjectX")
    assert len(dbs) == 2
    assert [d.databank_name for d in dbs] == ["Archive", "Results"]

    # 3. Add member and clear
    art_rec = art.store_artifact(b"strat_code", "text/plain")
    dbk.add_member(
        "ProjectX",
        "Results",
        art_rec.artifact_id,
        fitness=1.5,
        ranking_value=85.0,
        metrics={"net_profit": 1200.0},
    )
    assert len(dbk.get_members("ProjectX", "Results")) == 1

    cleared = dbk.clear_databank("ProjectX", "Results")
    assert cleared == 1
    assert len(dbk.get_members("ProjectX", "Results")) == 0

    # 4. Delete databank
    assert dbk.delete_databank("ProjectX", "Archive") is True
    assert dbk.get_databank("ProjectX", "Archive") is None


def test_member_ranking_and_capacity_eviction(tmp_path: Path) -> None:
    """Test deterministic eviction when databank capacity is reached."""
    _db, art, dbk = _setup_services(tmp_path)

    dbk.create_databank("ProjectA", "TopStrategies", capacity=2)

    s1 = art.store_artifact(b"s1", "text/plain")
    s2 = art.store_artifact(b"s2", "text/plain")
    s3 = art.store_artifact(b"s3", "text/plain")
    s4 = art.store_artifact(b"s4", "text/plain")

    # Fill databank to capacity (2 items)
    m1 = dbk.add_member(
        "ProjectA",
        "TopStrategies",
        s1.artifact_id,
        fitness=1.0,
        ranking_value=10.0,
        metrics={},
    )
    assert m1 is not None

    m2 = dbk.add_member(
        "ProjectA",
        "TopStrategies",
        s2.artifact_id,
        fitness=2.0,
        ranking_value=20.0,
        metrics={},
    )
    assert m2 is not None

    # Candidate s3 with lower ranking than lowest (5.0 < 10.0) -> Rejected
    m3 = dbk.add_member(
        "ProjectA",
        "TopStrategies",
        s3.artifact_id,
        fitness=0.5,
        ranking_value=5.0,
        metrics={},
    )
    assert m3 is None
    members_after_reject = dbk.get_members("ProjectA", "TopStrategies")
    assert len(members_after_reject) == 2
    assert [m.artifact_id for m in members_after_reject] == [
        s2.artifact_id,
        s1.artifact_id,
    ]

    # Candidate s4 with rank 15.0 -> Evicts s1 (rank 10.0), keeps s2 (rank 20.0)
    m4 = dbk.add_member(
        "ProjectA",
        "TopStrategies",
        s4.artifact_id,
        fitness=1.8,
        ranking_value=15.0,
        metrics={},
    )
    assert m4 is not None
    members_after_eviction = dbk.get_members("ProjectA", "TopStrategies")
    assert len(members_after_eviction) == 2
    assert [m.artifact_id for m in members_after_eviction] == [
        s2.artifact_id,
        s4.artifact_id,
    ]


def test_similarity_evaluation_and_dismissal(tmp_path: Path) -> None:
    """Test metric similarity evaluation and inferior fitness dismissal (DEC-PERSISTENCE-003)."""
    _db, art, dbk = _setup_services(tmp_path)

    dbk.create_databank("ProjectB", "Results", capacity=10)
    profile = SimilarityProfile(
        tolerance_pct=5.0,
        compare_net_profit=True,
        compare_trade_count=True,
        compare_drawdown=True,
    )

    # Strategy A
    s_a = art.store_artifact(b"strategy_a", "text/plain")
    m_a = dbk.add_member(
        "ProjectB",
        "Results",
        s_a.artifact_id,
        fitness=1.5,
        ranking_value=50.0,
        metrics={"net_profit": 1000.0, "trade_count": 100.0, "drawdown": 200.0},
    )
    assert m_a is not None

    # Candidate B: Similar (+2% profit, +1% trades, -2% DD) with LOWER fitness (1.2 < 1.5)
    s_b = art.store_artifact(b"strategy_b", "text/plain")
    m_b = dbk.add_member(
        "ProjectB",
        "Results",
        s_b.artifact_id,
        fitness=1.2,
        ranking_value=48.0,
        metrics={"net_profit": 1020.0, "trade_count": 101.0, "drawdown": 196.0},
        similarity_profile=profile,
    )
    assert m_b is None  # Dismissed as redundant/inferior

    # Candidate C: Similar (+2% profit, +1% trades, -2% DD) with HIGHER fitness (2.2 > 1.5)
    s_c = art.store_artifact(b"strategy_c", "text/plain")
    m_c = dbk.add_member(
        "ProjectB",
        "Results",
        s_c.artifact_id,
        fitness=2.2,
        ranking_value=60.0,
        metrics={"net_profit": 1020.0, "trade_count": 101.0, "drawdown": 196.0},
        similarity_profile=profile,
    )
    assert m_c is not None  # Admitted and replaced A!

    members = dbk.get_members("ProjectB", "Results")
    assert len(members) == 1
    assert members[0].artifact_id == s_c.artifact_id


def test_copy_and_move_member(tmp_path: Path) -> None:
    """Test copy and move operations across databanks."""
    _db, art, dbk = _setup_services(tmp_path)

    dbk.create_databank("ProjectX", "Source", capacity=10)
    dbk.create_databank("ProjectX", "Target", capacity=10)

    strat = art.store_artifact(b"strat_copy_move", "text/plain")
    dbk.add_member(
        "ProjectX",
        "Source",
        strat.artifact_id,
        fitness=1.9,
        ranking_value=90.0,
        metrics={"sharpe": 2.1},
    )

    # 1. Copy member
    copied = dbk.copy_member(
        "ProjectX",
        "Source",
        target_project="ProjectX",
        target_databank="Target",
        artifact_id=strat.artifact_id,
    )
    assert copied.artifact_id == strat.artifact_id
    assert len(dbk.get_members("ProjectX", "Source")) == 1
    assert len(dbk.get_members("ProjectX", "Target")) == 1

    # 2. Move member back from Target to Source (after removing from Source)
    dbk.remove_member("ProjectX", "Source", strat.artifact_id)
    assert len(dbk.get_members("ProjectX", "Source")) == 0

    moved = dbk.move_member(
        "ProjectX",
        "Target",
        target_project="ProjectX",
        target_databank="Source",
        artifact_id=strat.artifact_id,
    )
    assert moved.artifact_id == strat.artifact_id
    assert len(dbk.get_members("ProjectX", "Source")) == 1
    assert len(dbk.get_members("ProjectX", "Target")) == 0

    # 3. Failed move into missing target databank leaves source intact
    with pytest.raises(DatabankNotFoundError, match="Target databank"):
        dbk.move_member(
            "ProjectX",
            "Source",
            target_project="ProjectX",
            target_databank="NonExistentTarget",
            artifact_id=strat.artifact_id,
        )
    assert len(dbk.get_members("ProjectX", "Source")) == 1
    assert dbk.get_members("ProjectX", "Source")[0].artifact_id == strat.artifact_id


def test_databank_column_views(tmp_path: Path) -> None:
    """Test saving, retrieving, and listing column views."""
    _db, _art, dbk = _setup_services(tmp_path)

    view = DatabankViewConfig(
        view_name="QuantSummary",
        scope="global",
        columns=(
            ColumnConfig(
                name="Net Profit",
                metric_key="net_profit",
                sample_type=SampleType.FULL_SAMPLE,
                format_spec="{:.2f}",
                is_visible=True,
                sort_priority=1,
                sort_direction=RankingDirection.DESCENDING,
            ),
            ColumnConfig(
                name="Max DD",
                metric_key="drawdown",
                sample_type=SampleType.FULL_SAMPLE,
                format_spec="{:.1f}%",
                is_visible=True,
            ),
        ),
    )

    dbk.save_view(view)

    fetched = dbk.get_view("QuantSummary")
    assert fetched is not None
    assert fetched.view_name == "QuantSummary"
    assert len(fetched.columns) == 2
    assert fetched.columns[0].name == "Net Profit"

    all_views = dbk.list_views()
    assert any(v.view_name == "QuantSummary" for v in all_views)


def test_databank_error_handling(tmp_path: Path) -> None:
    """Test expected validation errors for databank operations."""
    _db, art, dbk = _setup_services(tmp_path)
    dbk.create_databank("Proj", "Bank", capacity=10)

    # Missing databank
    with pytest.raises(DatabankNotFoundError):
        dbk.add_member(
            "Proj",
            "NonExistent",
            "some_art",
            fitness=1.0,
            ranking_value=1.0,
            metrics={},
        )

    # Missing artifact
    with pytest.raises(ArtifactNotFoundError):
        dbk.add_member(
            "Proj", "Bank", "missing_art_id", fitness=1.0, ranking_value=1.0, metrics={}
        )

    # Duplicate member
    art_rec = art.store_artifact(b"content", "text/plain")
    dbk.add_member(
        "Proj", "Bank", art_rec.artifact_id, fitness=1.0, ranking_value=1.0, metrics={}
    )
    with pytest.raises(DuplicateMemberError):
        dbk.add_member(
            "Proj",
            "Bank",
            art_rec.artifact_id,
            fitness=1.0,
            ranking_value=1.0,
            metrics={},
        )


def test_databanks_feature_lifecycle(tmp_path: Path) -> None:
    """Test runtime composition of DatabankFeature."""

    async def _test() -> None:
        db_file = tmp_path / "runtime_dbk.db"
        art_dir = tmp_path / "runtime_artifacts"
        runtime = Runtime(
            [
                lambda: DatabaseFeature(DatabaseConfig(database_path=db_file)),
                lambda: ArtifactFeature(ArtifactConfig(artifacts_dir=art_dir)),
                lambda: DatabankFeature(DatabankConfig(default_capacity=50)),
            ]
        )
        async with runtime:
            dbk_service = runtime.require(DATABANK_STORE)
            rec = dbk_service.create_databank("P", "Test")
            assert rec.databank_name == "Test"

    asyncio.run(_test())


def test_databank_factory() -> None:
    """Test zero-argument factory returns DatabankFeature."""
    f = feature()
    assert isinstance(f, DatabankFeature)
    assert f.spec.name == "persistence.databanks"
