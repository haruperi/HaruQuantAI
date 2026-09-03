"""Feature specification for the API and event transport."""

from app.contracts.interfaces.capabilities import SERVE_API_EVENTS_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-IFACE-SERVE_API_EVENTS",
    domain="interfaces",
    provides=frozenset({SERVE_API_EVENTS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Serve versioned HTTP/OpenAPI contracts and SSE events.",
    state=None,
    config_keys=frozenset(
        {
            "supported_api_versions",
            "server_prefixes",
            "stream_retention_events",
            "stream_replay_batch_limit",
            "event_payload_max_bytes",
        }
    ),
)
