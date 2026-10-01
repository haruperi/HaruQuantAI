"""Self-contained deterministic sq_equity usage; authored input only."""

import pandas as pd  # type: ignore[import-untyped]
from app.plugin.DataSource.sq_equity import resample_candles


def main() -> None:
    """Aggregate authored minute bars with the source's OHLCV rules."""
    frame = pd.DataFrame(
        {
            "DateTime": pd.to_datetime(
                ["2024-01-02T12:00:00Z", "2024-01-02T12:01:00Z"]
            ),
            "Open": [1.0, 1.5],
            "High": [2.0, 3.0],
            "Low": [0.5, 1.0],
            "Close": [1.5, 2.5],
            "Volume": [4, 5],
        }
    )
    result = resample_candles(frame, "M5")
    assert result["Close"].tolist() == [2.5]
    assert result["Volume"].tolist() == [9]


if __name__ == "__main__":
    main()
