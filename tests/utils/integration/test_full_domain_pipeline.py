"""Structural checks for the real full-domain Utils usage pipeline."""

from __future__ import annotations

import runpy
from pathlib import Path

_PIPELINE = Path(__file__).parents[1] / "usage" / "features" / "features.py"


def test_full_domain_pipeline_declares_every_feature_and_stage() -> None:
    """Verify the standalone pipeline remains complete without dispatching it."""
    namespace = runpy.run_path(str(_PIPELINE), run_name="utils_pipeline_inspection")

    assert namespace["FEATURE_IDS"] == tuple(
        f"FEAT-UTIL-{number:02d}" for number in range(15)
    )
    assert len(namespace["STAGES"]) == 18
    assert callable(namespace["main"])


def test_full_domain_pipeline_keeps_real_notification_boundary() -> None:
    """Verify usage evidence retains the genuine notification integration call."""
    source = _PIPELINE.read_text(encoding="utf-8")

    assert 'run_real_notification_evidence("UTILS-FULL-PIPELINE")' in source
    assert "from app.utils import" in source
    assert "SUCCESS: complete 18-stage Utils domain pipeline completed" in source
