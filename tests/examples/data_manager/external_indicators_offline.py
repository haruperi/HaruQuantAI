"""Self-contained deterministic external_indicators usage; authored input only."""

from app.plugin.DataSource.external_indicators import ImportFormat, parse


def main() -> None:
    """Parse authored external values with an explicit immutable format."""
    descriptor = ImportFormat.model_validate(
        {
            "name": "Example",
            "separator": ",",
            "skipRows": 1,
            "skipColumns": 0,
            "dateFormat": "yyyy-MM-dd",
            "columns": ["Date", "Value 1"],
        }
    )
    records, ignored = parse("Date,Value\n2024-01-02,1.5", descriptor, 1, False)
    assert records == [{"timestamp": 1704153600000, "values": [1.5]}]
    assert ignored == 0


if __name__ == "__main__":
    main()
