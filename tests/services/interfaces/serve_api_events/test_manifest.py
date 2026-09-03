"""Unit tests for the serve-api-events manifest."""

from app.contracts.interfaces.capabilities import SERVE_API_EVENTS_CAPABILITY
from app.services.interfaces.serve_api_events.manifest import SPEC

_EXPECTED_CONFIG_KEYS = {
    "supported_api_versions",
    "server_prefixes",
    "stream_retention_events",
    "stream_replay_batch_limit",
    "event_payload_max_bytes",
}


def test_manifest_spec() -> None:
    """Verify feature specification constants and declarations."""
    assert SPEC.feature_id == "FEAT-IFACE-SERVE_API_EVENTS"
    assert SPEC.domain == "interfaces"
    assert SPEC.provides == frozenset({SERVE_API_EVENTS_CAPABILITY})
    assert SPEC.requires == frozenset()
    assert SPEC.optional == frozenset()
    assert SPEC.conflicts == frozenset()
    assert SPEC.state is None
    assert SPEC.config_keys == frozenset(_EXPECTED_CONFIG_KEYS)
    SPEC.validate()


def test_manifest_capability_identifier() -> None:
    """Verify the provided capability runtime identifier."""
    (capability,) = SPEC.provides
    assert capability.identifier == "interfaces.serve-api-events@1"
