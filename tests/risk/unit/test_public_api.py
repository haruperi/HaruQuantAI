"""Unit tests for the exact public Risk package port."""

from app.services import risk
from app.utils import get_standard_response_type

from tests.risk import _support as examples


def test_root_public_api_is_exact_and_resolvable() -> None:
    """Expose every approved standalone operation and no private state port."""
    expected = {name for name in risk.__all__ if callable(getattr(risk, name))}
    assert set(risk.__all__) == expected
    assert all(hasattr(risk, name) for name in risk.__all__)
    assert all(
        getattr(risk, name).__class__.__name__ == "function" for name in risk.__all__
    )
    assert not any(name.startswith("_") for name in risk.__all__)


def test_public_operation_uses_standard_response_boundary() -> None:
    """Expose raw Risk results inside the shared response envelope."""
    response = risk.compute_config_hash(examples._config())

    assert isinstance(response, get_standard_response_type())
    assert response.status == "success"
    assert len(response.data) == 64
    assert response.error is None
    assert response.metadata.domain == "risk"
    assert response.metadata.read_only is True
    assert response.metadata.places_trade is False
    assert response.metadata.requires_network is False
