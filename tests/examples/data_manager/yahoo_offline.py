"""Self-contained deterministic yahoo usage; authored input only."""

from app.plugin.DataSource.yahoo import normalize_timeframe, parse_date_param


def main() -> None:
    """Resolve source UTC dates and interval rules without a remote request."""
    assert normalize_timeframe("H4") == ("1h", "4h")
    assert parse_date_param("2024-01-02").isoformat() == "2024-01-02T00:00:00+00:00"


if __name__ == "__main__":
    main()
