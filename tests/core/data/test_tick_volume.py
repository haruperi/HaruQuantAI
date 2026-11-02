"""Recorded tick volumes remain exact and unknown observations remain unknown."""

import pandas as pd
import pyarrow as pa
import pytest
from app.core.data.market_storage import encode_frame
from app.workspace.data_manager.data.conversions import ticks_to_dataframe


def test_uint64_volume_survives_encoding_without_float_rounding(caplog):
    frame = pd.DataFrame(
        {
            "Bid": [1.1, 1.1, 1.1],
            "Ask": [1.2, 1.2, 1.2],
            "Volume": pd.array([2**63 + 7, None, 0], dtype="UInt64"),
        },
        index=pd.date_range("2025-01-01", periods=3, freq="s", tz="UTC"),
    )
    with caplog.at_level("DEBUG"):
        table = encode_frame(frame, "TICK", 0.00001)
    assert "FR-MARKET-STORAGE-tick-volume" in caplog.text
    assert table.schema.field("Volume").type == pa.uint64()
    assert table["Volume"].to_pylist() == [2**63 + 7, None, 0]
    assert table["Flags"].to_pylist() == [None, None, None]
    assert (
        encode_frame(frame.drop(columns="Volume"), "TICK", 0.00001)["Volume"].null_count
        == 3
    )


@pytest.mark.parametrize("volume", [-1, 1.5, 2**64])
def test_invalid_volume_is_rejected(volume):
    frame = pd.DataFrame(
        {"Bid": [1.1], "Ask": [1.2], "Volume": [volume]},
        index=pd.to_datetime(["2025-01-01T00:00:00Z"]),
    )
    with pytest.raises(ValueError):
        encode_frame(frame, "TICK", 0.00001)


def test_conversion_retains_recorded_volume_and_missing_values():
    frame = ticks_to_dataframe(
        [
            {"time_msc": 1700000000000, "bid": 1.1, "ask": 1.2, "volume": 2**63 + 7},
            {"time_msc": 1700000000001, "bid": 1.1, "ask": 1.2},
        ]
    )
    assert frame["Volume"].iloc[0] == 2**63 + 7
    assert pd.isna(frame["Volume"].iloc[1])


def test_update_normalizes_old_schema_and_preserves_known_volume(tmp_path):
    import pyarrow.parquet as pq
    from app.workspace.data_manager.data.storage import _merge_partition

    date = pd.Timestamp("2025-01-01T00:00:00Z").to_pydatetime()
    frame = pd.DataFrame(
        {"Bid": [1.1], "Ask": [1.2], "Flags": [3]}, index=pd.to_datetime([date])
    )
    old = encode_frame(frame, "TICK", 0.00001).drop(["Volume"])
    original = tmp_path / "original.parquet"
    pq.write_table(old, original)
    incoming = encode_frame(
        frame.assign(Volume=pd.array([17], dtype="UInt64")), "TICK", 0.00001
    )
    paths = _merge_partition(
        [str(original)],
        incoming,
        tmp_path / "result.parquet",
        "TICK",
        overwrite=False,
        lower=date,
        upper=date,
        context=None,
        created=[],
    )
    assert pq.read_table(paths[0])["Volume"].to_pylist() == [17]
    unknown = encode_frame(frame, "TICK", 0.00001)
    final = _merge_partition(
        paths,
        unknown,
        tmp_path / "next.parquet",
        "TICK",
        overwrite=False,
        lower=date,
        upper=date,
        context=None,
        created=[],
    )
    assert pq.read_table(final[0])["Volume"].to_pylist() == [17]
    different = encode_frame(frame.assign(Volume=18), "TICK", 0.00001)
    more = _merge_partition(
        final,
        different,
        tmp_path / "other.parquet",
        "TICK",
        overwrite=False,
        lower=date,
        upper=date,
        context=None,
        created=[],
    )
    assert sorted(pq.read_table(more[0])["Volume"].to_pylist()) == [17, 18]
