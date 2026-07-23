"""Validate Brokers feature-registry and active-document parity."""

import re
from pathlib import Path


def test_brokers_readme_has_one_reconciled_partial_registry() -> None:
    """Require one feature, folder, and usage program for every registry row."""
    readme = Path("app/services/brokers/README.md").read_text(encoding="utf-8")
    assert readme.count("### Feature Registry") == 1
    rows = re.findall(
        r"\| Partial \| `(?P<id>FEAT-BRK-\d{2})`[^|]*"
        r"\| `(?P<folder>[^`]+/)`[^|]*\|[^|]*\|[^|]*"
        r"\| `(?P<usage>tests/brokers/usage/\d{2}_[^`]+\.py)` \|",
        readme,
    )
    assert [feature_id for feature_id, _, _ in rows] == [
        f"FEAT-BRK-{index:02d}" for index in range(16)
    ]
    assert len({folder for _, folder, _ in rows}) == 16
    assert len({usage for _, _, usage in rows}) == 16
    for _, folder, usage in rows:
        assert (Path("app/services/brokers") / folder).is_dir()
        assert Path(usage).is_file()
    assert "aggregates midpoint bars locally" not in readme
    assert "without a probe" not in readme
    assert "- [x]" not in readme
