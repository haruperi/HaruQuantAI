"""Feature specification for Unified CLI and MCP Automation."""

from app.contracts.interfaces.capabilities import AUTOMATE_COMMANDS_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-IFACE-AUTOMATE_COMMANDS",
    domain="interfaces",
    provides=frozenset({AUTOMATE_COMMANDS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Wrap application services through cli/mcp and portable manifests.",
    config_keys=frozenset(
        {
            "title",
            "command_timeout_seconds",
            "max_durable_jobs",
            "enable_mcp",
        }
    ),
)
