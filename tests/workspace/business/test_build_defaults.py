"""Unit tests for fixed-size build defaults and attribute projections.

Description:
    Tests FixedSizeBuildSettings dataclass immutability and the
    FixedSizeBuildProjection.attributes deterministic projection logic.

Purpose:
    FEAT-APP-BUSINESS: Unit test verification of build attribute projections.

Key Capabilities:
    - FR-TEST-DEFAULT-PROJECTION: Absent settings yield exact default attributes.
    - FR-TEST-LITERAL-PROJECTION: Provided settings yield literal string values.

Python API Usage:
    ```python
    uv run python -m pytest tests/workspace/business/test_build_defaults.py -q
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/business/test_build_defaults.py --cov=app/workspace/business
    ```
"""

from __future__ import annotations

from app.workspace.business.build_defaults import (
    FixedSizeBuildProjection,
    FixedSizeBuildSettings,
)


def test_absent_settings_defaults() -> None:
    """Verify None settings yields default dictionary and prevents shared mutation."""
    expected = {
        "use": "false",
        "name": "-fixedSize",
        "lots": "0.01",
        "platform": "mql4",
    }
    attrs1 = FixedSizeBuildProjection.attributes(None)
    assert attrs1 == expected

    # Mutate returned dictionary
    attrs1["use"] = "true"
    attrs1["lots"] = "1.00"

    # Subsequent call must be completely unaffected
    attrs2 = FixedSizeBuildProjection.attributes(None)
    assert attrs2 == expected


def test_provided_attributes_remain_literal() -> None:
    """Verify provided settings are preserved literally without clamping or altering."""
    settings = FixedSizeBuildSettings(
        enabled=True,
        name=" custom ",
        lots="0.20",
        platform="mql5",
    )
    result = FixedSizeBuildProjection.attributes(settings)
    expected = {
        "use": "true",
        "name": " custom ",
        "lots": "0.20",
        "platform": "mql5",
    }
    assert result == expected

    # Test false enabled
    settings_false = FixedSizeBuildSettings(
        enabled=False,
        name="test",
        lots="0.05",
        platform="mql4",
    )
    result_false = FixedSizeBuildProjection.attributes(settings_false)
    assert result_false["use"] == "false"
