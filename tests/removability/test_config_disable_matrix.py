"""Fast configuration-disablement checks for discovered optional providers."""

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
    """Verify generated provider cases are nonempty and deterministic."""
    assert _CASES
    provider_ids = [str(case["provider_id"]) for case in _CASES]
    assert provider_ids == sorted(provider_ids)

    for case in _CASES:
        assert "provider_id" in case
        assert case["tier"] in ("A", "B")
        assert case["provided_capabilities"]
        assert case["expected_reason"] == "DISABLED"


@pytest.mark.parametrize("case", _CASES, ids=lambda case: str(case["provider_id"]))
def test_optional_provider_config_disablement(case: dict[str, Any]) -> None:
    """Verify discovery and core imports survive each generated provider case."""
    assert run_disable_case(case, _REPO_ROOT), (
        f"Failed configuration-disablement case for {case['provider_id']}"
    )
