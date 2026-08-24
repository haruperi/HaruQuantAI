"""Feature specification for HTTP and Event Contracts."""

from app.contracts.interfaces.capabilities import SERVE_API_EVENTS_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-IFACE-SERVE_API_EVENTS",
    domain="interfaces",
    provides=frozenset({SERVE_API_EVENTS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Expose versioned, idempotent, paged, bounded HTTP/SSE resources.",
    config_keys=frozenset(
        {
            "title",
            "api_version",
            "event_buffer_size",
            "max_artifact_download_bytes",
        }
    ),
)
