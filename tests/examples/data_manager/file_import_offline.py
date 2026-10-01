"""Self-contained deterministic file_import usage; authored input only."""

from app.plugin.DataSource.file_import import FileRequest, FormatSpec, parse_request


def main() -> None:
    """Parse explicit authored CSV without files, databases or network."""
    request = FileRequest(
        content="2024.01.02,12:00,1,2,0.5,1.5,4",
        symbol="EURUSD",
        format=FormatSpec(
            name="Example",
            separator=",",
            date_format="yyyy.MM.dd",
            time_format="HH:mm",
            columns=("Date", "Time", "Open", "High", "Low", "Close", "Volume"),
        ),
    )
    frame, timeframe = parse_request(request)
    assert timeframe == "M1"
    assert frame["close"].tolist() == [1.5]


if __name__ == "__main__":
    main()
