"""Unit tests for datasets, provider downloads, custom data, quality, and transforms."""

from __future__ import annotations

from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]
import pytest
from app.host.persistence.create import create_schema
from app.host.persistence.read import resolve_connection
from app.host.transport import EventBus
from app.workspace.data_manager import (
    MarketBar,
    connections,
    custom_data,
)
from app.workspace.data_manager import (
    data as data_mod,
)
from app.workspace.data_manager.actions.review import quality as quality_mod
from app.workspace.data_manager.actions.review.quality import DataQualityInspector
from app.workspace.data_manager.actions.transform import transforms as transform_mod
from app.workspace.data_manager.actions.transform.transforms import (
    CloneTimezoneConfig,
    ResampleConfig,
    SeriesTransformer,
)
from app.workspace.data_manager.connections import (
    ProviderConnectionsService,
)
from app.workspace.data_manager.custom_data import CustomDataService
from app.workspace.data_manager.data import DataManagerDataService
from app.workspace.data_manager.log import DataManagerLogService
from app.workspace.data_manager.sessions import SessionWindow, TradingSession


@pytest.fixture
def test_db_path(tmp_path: Path) -> Path:
    """Fixture providing initialized SQLite database file path."""
    db_file = tmp_path / "test_datamgr_2.db"
    with resolve_connection(db_file) as conn:
        create_schema(conn)
    return db_file


# ============================================================================
# 1. DataManagerDataService Tests
# ============================================================================


def test_data_service_lifecycle_and_exports(test_db_path: Path, tmp_path: Path) -> None:
    """Test dataset catalog CRUD, Parquet bar I/O, review slices, and exports."""
    log_svc = DataManagerLogService(db_path=test_db_path)
    service = DataManagerDataService(
        db_path=test_db_path,
        data_dir=tmp_path / "data",
        log_service=log_svc,
    )

    sample_csv = "timestamp,open,high,low,close,volume,spread\n" + "\n".join(
        f"2026-01-01 {i // 60:02d}:{i % 60:02d}:00,1.1000,1.1005,1.0995,1.1002,150,1"
        for i in range(100)
    )
    rec = service.import_dataset(
        {
            "symbol": "EURUSD",
            "timeframe": "M1",
            "source": "dukascopy",
            "csv_content": sample_csv,
        }
    )
    assert rec.id == "dukascopy:EURUSD"
    assert rec.bars >= 100
    assert rec.to_data_info().symbol == "EURUSD"

    # Parquet read/write roundtrip
    df = service.read_bars_dataframe(rec.id)
    assert len(df) == rec.bars
    assert "open" in df.columns and "close" in df.columns

    # Chart review slicing
    chart_bars = service.get_review_chart_bars("EURUSD", max_bars=10, dataset_id=rec.id)
    assert len(chart_bars) == 10
    assert chart_bars[0]["open"] > 0
    assert "datetime" in chart_bars[0]

    # Review tabular rows and edits
    rows = service.get_review_rows(rec.id, limit=5, offset=0)
    assert len(rows) == 5

    first_ts = rows[0]["timestamp"]
    save_res = service.save_review_changes(
        rec.id,
        changed_bars=[{"timestamp": first_ts, "open": 1.2345}],
        deleted_timestamps=[],
    )
    assert save_res["updated_count"] == 1
    reloaded_df = service.read_bars_dataframe(rec.id)
    assert reloaded_df["open"].iloc[0] == 1.2345

    # Index for date
    idx = service.get_index_for_date(rec.id, first_ts)
    assert idx == 0

    # CSV Formats
    service.save_csv_format(
        {
            "name": "Custom Format",
            "delimiter": ";",
            "columns": ["Date", "Open", "Close"],
        }
    )
    formats = service.list_csv_formats()
    assert any(f["name"] == "Custom Format" for f in formats)
    service.delete_csv_format("Custom Format")

    # Multi-format exports
    csv_exp = service.export_datasets({"dataset_ids": [rec.id], "format": "CSV"})
    assert csv_exp["exported_count"] == 1
    assert "DateTime,Open" in csv_exp["artifacts"][0]["content"]

    mt4_exp = service.export_datasets({"dataset_ids": [rec.id], "format": "MT4"})
    assert mt4_exp["exported_count"] == 1
    assert "." in mt4_exp["artifacts"][0]["content"]

    mt5_exp = service.export_datasets({"dataset_ids": [rec.id], "format": "MT5"})
    assert mt5_exp["exported_count"] == 1
    assert "<DATE>" in mt5_exp["artifacts"][0]["content"]

    # Clear and delete
    cleared = service.clear_dataset(rec.id)
    assert cleared["cleared"] is True
    reloaded = service.get_dataset(rec.id)
    assert reloaded is not None and reloaded.bars == 0

    del_res = service.delete_dataset(rec.id)
    assert del_res["deleted"] is True
    assert service.get_dataset(rec.id) is None

    # Mass actions
    r1 = service.import_dataset(
        {"symbol": "GBPUSD", "timeframe": "M1", "csv_content": sample_csv}
    )
    mass_res = service.mass_delete_datasets([str(r1.id)], action="remove")
    assert mass_res["affected_count"] == 1

    data_mod.main()


# ============================================================================
# 2. ProviderConnectionsService Tests
# ============================================================================


class _MockTestProvider:
    provider_id: str = "dukascopy"
    display_name: str = "Dukascopy Mock"
    supported_timeframes: tuple[str, ...] = ("M1", "H1", "D1")

    def fetch_bars(
        self,
        symbol: str,
        _timeframe: str,
        _date_from: str,
        _date_to: str,
    ) -> list[MarketBar]:
        del symbol
        base_epoch = 1767225600
        return [
            MarketBar(
                time=base_epoch + i * 60,
                open=1.1000 + i * 0.0001,
                high=1.1005 + i * 0.0001,
                low=1.0995 + i * 0.0001,
                close=1.1002 + i * 0.0001,
                tick_volume=150,
                spread=1,
            )
            for i in range(200)
        ]


def test_provider_connections_service(test_db_path: Path, tmp_path: Path) -> None:
    """Test data providers, health probing, and download orchestration with EventBus."""
    data_svc = DataManagerDataService(db_path=test_db_path, data_dir=tmp_path / "data")
    log_svc = DataManagerLogService(db_path=test_db_path)
    bus = EventBus()

    _, queue, _, _ = bus.subscribe(["databanks"])

    conn_svc = ProviderConnectionsService(
        db_path=test_db_path,
        data_dir=tmp_path / "data",
        data_service=data_svc,
        log_service=log_svc,
        event_bus=bus,
    )
    conn_svc.register_adapter("dukascopy", _MockTestProvider())

    providers = conn_svc.list_providers()
    assert len(providers) >= 7
    assert conn_svc.active_providers_count() >= 7

    duka = conn_svc.check_connection("dukascopy")
    assert duka.connected is True
    assert "M1" in duka.supported_timeframes

    unknown = conn_svc.check_connection("unknown_feed")
    assert unknown.connected is False

    # Download job
    job_res = conn_svc.download_historical_data(
        {
            "provider": "dukascopy",
            "symbol": "EURUSD",
            "timeframe": "M1",
        }
    )
    assert job_res.bars_downloaded == 200
    assert not queue.empty()
    ev = queue.get_nowait()
    assert ev.payload["dataset_id"] == "dukascopy:EURUSD_M1"

    connections.main()


# ============================================================================
# 3. CustomDataService Tests
# ============================================================================


def test_custom_data_service(test_db_path: Path, tmp_path: Path) -> None:
    """Test external indicators, CSV series import, and MQ4 buffer recognition."""
    service = CustomDataService(db_path=test_db_path, data_dir=tmp_path / "data")

    defn = service.save_definition(
        {
            "name": "COT_Gold",
            "values": [{"name": "Commercial_Net", "mt4": "", "mt5": "", "el": ""}],
        }
    )
    assert defn.name == "COT_Gold"

    csv_data = (
        "2026-01-01,15000\n2026-01-08,16200\n2026-01-15,14800\n2026-01-22,17100\n"
    )
    imported = service.import_csv_records("COT_Gold", csv_data)
    assert imported.total_days == 4
    assert len(imported.records) == 4

    # List & get
    all_defs = service.list_definitions()
    assert len(all_defs) == 1
    reloaded = service.get_definition("COT_Gold")
    assert reloaded is not None and reloaded.total_days == 4

    # MQ4 recognition
    mq4_code = """
    #property indicator_buffers 3
    void init() {
        SetIndexBuffer(0, Buf1);
        SetIndexLabel(0, "FastEMA");
        SetIndexBuffer(1, Buf2);
        SetIndexLabel(1, "SlowEMA");
        SetIndexBuffer(2, Buf3);
        SetIndexLabel(2, "MACD_Line");
    }
    """
    mq4_def = service.recognize_mq4("MACD_Custom.mq4", mq4_code)
    assert mq4_def.name == "MACD_Custom"
    assert len(mq4_def.values) == 3
    assert mq4_def.values[0].name == "FastEMA"
    assert "iCustom" in mq4_def.values[0].mt4

    # Clear and delete
    cleared = service.clear_definition("COT_Gold")
    assert cleared.total_days == 0
    assert service.delete_definition("COT_Gold") is True
    assert service.get_definition("COT_Gold") is None

    custom_data.main()


# ============================================================================
# 4. DataQualityInspector Tests
# ============================================================================


def test_data_quality_inspector(test_db_path: Path, tmp_path: Path) -> None:
    """Test data quality checks, envelope violations, spike detection, and scoring."""
    data_svc = DataManagerDataService(db_path=test_db_path, data_dir=tmp_path / "data")
    inspector = DataQualityInspector(
        db_path=test_db_path,
        data_service=data_svc,
        spike_threshold_pct=0.05,
    )

    # Clean dataset with explicit bars
    clean_csv = "timestamp,open,high,low,close,volume,spread\n" + "\n".join(
        f"2026-10-12 10:{i:02d}:00,1.1000,1.1005,1.0995,1.1002,100,1" for i in range(20)
    )
    clean_rec = data_svc.import_dataset(
        {"symbol": "CLEAN", "timeframe": "M1", "csv_content": clean_csv}
    )
    clean_rep = inspector.inspect_dataset(str(clean_rec.id))
    assert clean_rep.quality_score >= 0.95

    # Synthesize anomalies including NaN and intra-day gap
    bad_rows = [
        {
            "timestamp": "2026-10-12 10:00:00",
            "open": 1.1000,
            "high": 1.1050,
            "low": 1.0950,
            "close": 1.1020,
            "volume": 100,
        },
        {
            "timestamp": "2026-10-12 10:01:00",
            "open": -1.0,
            "high": 1.1050,
            "low": 1.0950,
            "close": 1.1020,
            "volume": 100,
        },  # Non-positive
        {
            "timestamp": "2026-10-12 10:02:00",
            "open": 1.1000,
            "high": 1.0900,
            "low": 1.0950,
            "close": 1.0920,
            "volume": 100,
        },  # High < Low
        {
            "timestamp": "2026-10-12 10:02:00",
            "open": 1.1000,
            "high": 1.1050,
            "low": 1.0950,
            "close": 1.1020,
            "volume": 100,
        },  # Duplicate TS
        {
            "timestamp": "2026-10-17 12:00:00",
            "open": 1.1000,
            "high": 1.1050,
            "low": 1.0950,
            "close": 1.1020,
            "volume": 100,
        },  # Weekend (Saturday)
        {
            "timestamp": "2026-10-19 10:00:00",
            "open": 1.1000,
            "high": 1.3000,
            "low": 1.0950,
            "close": 1.2500,
            "volume": 100,
        },  # Spike > 5%
        {
            "timestamp": "2026-10-19 18:00:00",
            "open": 1.1000,
            "high": 1.1050,
            "low": 1.0950,
            "close": float("nan"),
            "volume": 100,
        },  # Invalid numeric (NaN) + 8h intra-day gap
    ]
    bad_df = pd.DataFrame(bad_rows)
    bad_rec = data_svc.upsert_dataset({"id": "file:ANOMALIES"}, bars_df=bad_df)

    rep = inspector.inspect_dataset(str(bad_rec.id))
    assert rep.anomaly_counts["NON_POSITIVE_PRICE"] >= 1
    assert rep.anomaly_counts["OHLC_ENVELOPE_VIOLATION"] >= 1
    assert rep.anomaly_counts["DUPLICATE_TIMESTAMP"] >= 1
    assert rep.anomaly_counts["WEEKEND_BAR"] >= 1
    assert rep.anomaly_counts["PRICE_SPIKE"] >= 1
    assert rep.anomaly_counts["INVALID_NUMERIC"] >= 1
    assert rep.anomaly_counts["GAP_DETECTED"] >= 1
    assert rep.quality_score < 1.0

    # Summary and details
    summary = inspector.get_quality_summary(str(bad_rec.id))
    assert summary["dataset_id"] == bad_rec.id
    assert summary["total_anomalies"] >= 7

    details = inspector.get_quality_details(str(bad_rec.id), limit=2, offset=0)
    assert len(details["anomalies"]) == 2

    # Invalidate quality report
    inspector.invalidate_report(str(bad_rec.id))
    reset_summary = inspector.get_quality_summary(str(bad_rec.id))
    assert reset_summary["quality_score"] == 0.0

    quality_mod.main()


# ============================================================================
# 5. SeriesTransformer Tests
# ============================================================================


def test_series_transformer(test_db_path: Path, tmp_path: Path) -> None:
    """Test timeframe resampling, timezone cloning, and session filtering."""
    data_svc = DataManagerDataService(db_path=test_db_path, data_dir=tmp_path / "data")
    log_svc = DataManagerLogService(db_path=test_db_path)
    transformer = SeriesTransformer(data_service=data_svc, log_service=log_svc)

    sample_csv = "timestamp,open,high,low,close,volume,spread\n" + "\n".join(
        f"2026-01-01 {i // 60:02d}:{i % 60:02d}:00,1.1000,1.1005,1.0995,1.1002,150,1"
        for i in range(100)
    )
    source_rec = data_svc.import_dataset(
        {
            "symbol": "EURUSD",
            "timeframe": "M1",
            "source": "file",
            "csv_content": sample_csv,
        }
    )
    assert source_rec.bars >= 100

    # Resample M1 -> M5
    resampled = transformer.resample_dataset(
        ResampleConfig(dataset_id=str(source_rec.id), target_timeframe="M5")
    )
    assert resampled.timeframe == "M5"
    assert resampled.bars > 0
    assert resampled.bars < source_rec.bars

    # Enforce resolution hierarchy: rejecting downsampling M5 -> M1
    with pytest.raises(ValueError, match="Cannot downsample"):
        transformer.resample_dataset(
            ResampleConfig(dataset_id=str(resampled.id), target_timeframe="M1")
        )

    # Clone timezone +2 hours and remove weekends
    cloned = transformer.clone_timezone(
        CloneTimezoneConfig(
            dataset_id=str(source_rec.id),
            shift_hours=2,
            remove_weekends=True,
            postfix="_EET",
        )
    )
    assert "_EET" in str(cloned.id)
    assert cloned.bars > 0

    # Rejection of invalid IANA timezone
    with pytest.raises(ValueError, match="Unknown or invalid timezone"):
        transformer.clone_timezone(
            CloneTimezoneConfig(
                dataset_id=str(source_rec.id),
                timezone_type="iana",
                timezone="Invalid/Timezone_Name",
            )
        )

    # Session filter
    session = TradingSession(
        name="Forex RTH",
        windows=[
            SessionWindow(
                day_from="Mon",
                day_to="Fri",
                start_time="08:00",
                end_time="17:00",
            )
        ],
    )
    df = data_svc.read_bars_dataframe(str(source_rec.id))
    filtered = transformer.apply_session_filter(df, session)
    assert len(filtered) <= len(df)

    transform_mod.main()
