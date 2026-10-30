"""Fixed-size build settings and XML attribute projection.

Description:
    Provides attribute projection for StrategyQuant / HaruQuant strategy
    product build configurations. Converts fixed-size lot settings into
    standard XML attribute mappings for LockedToFixedSize nodes.

Purpose:
    FEAT-APP-BUSINESS: Business strategy packaging and fixed-size projections.

Key Capabilities:
    - FR-BUSINESS-FIXED-SIZE-SETTINGS: Frozen typed settings definition.
    - FR-BUSINESS-FIXED-SIZE-PROJECTION: Deterministic attribute projection.

Python API Usage:
    ```python
    from app.workspace.business.build_defaults import (
        FixedSizeBuildProjection,
        FixedSizeBuildSettings,
    )

    settings = FixedSizeBuildSettings(
        enabled=True,
        name="custom",
        lots="0.10",
        platform="mql5",
    )
    attrs = FixedSizeBuildProjection.attributes(settings)
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/business/test_build_defaults.py -q
    ```
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class FixedSizeBuildSettings:
    """Settings specifying fixed-size lot constraints for strategy builds."""

    enabled: bool
    name: str
    lots: str
    platform: str


class FixedSizeBuildProjection:
    """Projects fixed-size build settings to literal XML attribute dictionaries."""

    _DEFAULT_ATTRIBUTES: ClassVar[dict[str, str]] = {
        "use": "false",
        "name": "-fixedSize",
        "lots": "0.01",
        "platform": "mql4",
    }

    @classmethod
    def attributes(cls, settings: FixedSizeBuildSettings | None) -> dict[str, str]:
        """Project settings to a fresh dictionary of XML attributes.

        Args:
            settings: FixedSizeBuildSettings instance or None.

        Returns:
            New dictionary containing 'use', 'name', 'lots', and 'platform'.
        """
        if settings is None:
            return dict(cls._DEFAULT_ATTRIBUTES)

        return {
            "use": "true" if settings.enabled else "false",
            "name": settings.name,
            "lots": settings.lots,
            "platform": settings.platform,
        }
