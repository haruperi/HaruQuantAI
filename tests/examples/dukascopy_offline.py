"""Offline Dukascopy decoder and canonical Parquet publication example."""

import lzma
import struct
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pyarrow as pa  # type: ignore[import-untyped]
from app.persistence.market import TICK_SCHEMA, MarketDataStore, create_isolated_schema
from app.plugin.DataSource.dukascopy import decode_ticks


def main() -> None:
    """Decode an authored fixture and publish it only to a temporary store."""
    hour = datetime(2020, 4, 2, tzinfo=UTC)
    payload = lzma.compress(
        struct.pack(">IIIff", 10, 123456, 123450, 0.01, 0.02),
        format=lzma.FORMAT_ALONE,
    )
    rows = decode_ticks(payload, hour, "CHFJPY")
    with TemporaryDirectory() as directory:
        root = Path(directory)
        database = root / "database" / "haruquantai.db"
        create_isolated_schema(database)
        columns = list(zip(*rows, strict=True))
        table = pa.Table.from_arrays(
            [
                pa.array(values, type=field.type)
                for values, field in zip(columns, TICK_SCHEMA, strict=True)
            ],
            schema=TICK_SCHEMA,
        )
        store = MarketDataStore(root, database)
        record = store.publish(
            source="dukascopy",
            kind="ticks",
            symbol="chfjpy",
            period="2020-04",
            table=table,
            coverage=((rows[0][0], rows[-1][0]),),
            provider_mode="standard",
        )
        assert record.row_count == 1
        assert record.relative_path.endswith("ticks/chfjpy/2020/04-apr.parquet")


if __name__ == "__main__":
    main()
