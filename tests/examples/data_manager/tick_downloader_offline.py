"""Self-contained deterministic tick_downloader usage; authored input only."""

import lzma
import struct
from datetime import UTC, datetime

from app.plugin.DataSource.tick_downloader_import import _read_tick_file


def main() -> None:
    """Decode an authored BI5 hourly record without reading a donor directory."""
    raw = lzma.compress(
        struct.pack(">iiiff", 123, 123456, 123450, 0.125, 0.25),
        format=lzma.FORMAT_ALONE,
    )
    arrays = _read_tick_file(raw, datetime(2024, 1, 1, tzinfo=UTC), 5)
    assert arrays is not None
    assert arrays[0].tolist() == [1704067200123]
    assert arrays[1].tolist() == [1.23456]


if __name__ == "__main__":
    main()
