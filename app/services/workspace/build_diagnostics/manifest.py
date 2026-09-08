"""Feature specification for Workspace diagnostics."""

from app.contracts.orchestration.capabilities import MANAGE_JOBS_CAPABILITY
from app.contracts.workspace.capabilities import ARTIFACTS_CAPABILITY, BUILD_DIAGNOSTICS_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-WS-BUILD_DIAGNOSTICS", domain="workspace",
    provides=frozenset({BUILD_DIAGNOSTICS_CAPABILITY}),
    requires=frozenset({ARTIFACTS_CAPABILITY, MANAGE_JOBS_CAPABILITY}),
    optional=frozenset(), conflicts=frozenset(),
    description="Expose bounded redacted current diagnostics and identity-matched benchmark comparisons.",
    state=None, config_keys=frozenset({"max_records", "max_bytes"}),
)
