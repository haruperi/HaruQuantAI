"""Fast gated configuration disablement tests for all optional providers.

Traces to: P11-T01, Gate G11
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from scripts.architecture.provider_disable_matrix import (
    generate_disable_cases,
    run_disable_case,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CASES = generate_disable_cases(_REPO_ROOT)


def test_generator_schema_and_ordering() -> None:
    """Verify generated disable matrix conforms to schema and is deterministically ordered."""
    assert len(_CASES) > 0
    provider_ids = [str(c["provider_id"]) for c in _CASES]
    assert provider_ids == sorted(provider_ids)

    for case in _CASES:
        assert "provider_id" in case
        assert case["tier"] in ("A", "B")
        assert len(case["provided_capabilities"]) >= 1
        assert case["expected_reason"] == "DISABLED"


@pytest.mark.parametrize("case", _CASES, ids=lambda c: str(c["provider_id"]))
def test_optional_provider_config_disablement(case: dict[str, Any]) -> None:
    """Verify application boots and isolates when an optional provider is disabled."""
    success = run_disable_case(case, _REPO_ROOT)
    assert success is True, f"Failed config disablement for {case['provider_id']}"
