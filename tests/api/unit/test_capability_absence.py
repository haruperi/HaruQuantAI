"""Unit evidence for optional-capability absence tolerance in composition."""

from __future__ import annotations

import pytest
from app.services.api.composition.capabilities import (
    get_capability_id,
    get_optional_capability_ids,
    import_capability_attribute,
    import_capability_module,
    is_optional_capability,
)

_WIDGETS = "app.services.api.widgets"


def test_optional_capability_ids_are_the_approved_set() -> None:
    """Only capabilities consumed by the API alone may degrade."""
    assert get_optional_capability_ids() == frozenset(
        {"agentic", "analytics", "optimization", "portfolio", "research"}
    )
    for capability_id in ("trading", "risk", "data", "simulator", "indicators"):
        assert not is_optional_capability(capability_id)


def test_capability_id_is_the_provider_name_prefix() -> None:
    """Provider names carry their owning capability as the first segment."""
    assert get_capability_id("research.source") == "research"
    assert get_capability_id("trading.cancel_all_preflight_source") == "trading"


def test_absent_optional_capability_resolves_to_nothing() -> None:
    """An absent optional capability yields no module and no provider."""
    module = import_capability_module(
        f"{_WIDGETS}.research.absent_module",
        capability_id="research",
    )
    assert module is None
    attribute = import_capability_attribute(
        f"{_WIDGETS}.research.absent_module",
        "_research_source",
        capability_id="research",
    )
    assert attribute is None


def test_absent_required_capability_still_raises() -> None:
    """A required capability's absence fails closed instead of degrading."""
    with pytest.raises(ModuleNotFoundError):
        import_capability_module(
            f"{_WIDGETS}.trading.absent_module",
            capability_id="trading",
        )


def test_unrelated_missing_module_is_never_swallowed() -> None:
    """A failure outside the capability's own packages propagates."""
    with pytest.raises(ModuleNotFoundError):
        import_capability_module(
            "totally_unrelated_missing_package",
            capability_id="research",
        )


def test_present_capability_resolves_its_provider() -> None:
    """A present optional capability supplies its declared route dependency."""
    source = import_capability_attribute(
        f"{_WIDGETS}.research.routes",
        "_research_source",
        capability_id="research",
    )
    assert callable(source)
