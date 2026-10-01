"""Self-contained deterministic mt5 usage; authored input only."""

import sys
from pathlib import Path

if __name__ == "__main__" and not __package__:
    repo_root = str(Path(__file__).resolve().parents[3])
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

from app.plugin.DataSource.mt5 import (
    QDMAnalyzer,
    get_price_symbol_info,
    resample_candles,
    ticks_to_m1,
)


def main() -> None:
    """Transform authored historical ticks and verify specs without launching a terminal."""
    frame = ticks_to_m1(
        [{"time": "2024-01-02T12:00:01Z", "bid": 1.2, "ask": 1.3, "volume": 4}]
    )
    assert frame["Close"].tolist() == [1.2]
    assert frame["Volume"].tolist() == [4]

    resampled = resample_candles(frame, "M5")
    assert resampled["Close"].tolist() == [1.2]

    eurusd_info = get_price_symbol_info("EURUSD")
    assert eurusd_info["tick_size"] == 0.0001

    analyzer = QDMAnalyzer()
    assert analyzer.pip_size == 0.0001


if __name__ == "__main__":
    main()
