"""Self-contained deterministic darwinex usage; authored input only."""

from app.plugin.DataSource.darwinex import DarwinexFileImporter


def main() -> None:
    """Decode paired authored logs using source carry-forward and volume units."""
    arrays = DarwinexFileImporter.merge_ask_bid_files(
        b"1704067200123,1.2,90\n", b"1704067200124,1.1,1.75\n"
    )
    assert arrays[0].tolist() == [1704067200123, 1704067200124]
    assert arrays[1].tolist() == [1200000, 1200000]
    assert arrays[2].tolist() == [0, 1100000]
    assert arrays[3].tolist() == [0, 175000]


if __name__ == "__main__":
    main()
