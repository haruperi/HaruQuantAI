"""Feature specification for Agentic operations/readiness."""

from app.contracts.agentic.capabilities import MANDATE_CAPABILITY, OPERATIONS_CAPABILITY
from app.contracts.workspace.capabilities import PERSISTENCE_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-AGT-OPERATE_RUNS",
    domain="agentic",
    provides=frozenset({OPERATIONS_CAPABILITY}),
    requires=frozenset({MANDATE_CAPABILITY, PERSISTENCE_CAPABILITY}),
    optional=frozenset(), conflicts=frozenset(),
    description="Record redacted Agentic operations and durable containment/readiness decisions; validate replay without side effects.",
    state=StateDeclaration(namespace="agentic.operations", schema_version=1, retention_policy=RetentionPolicy.RETAIN, description="Redacted operation journal and containment decisions."),
    config_keys=frozenset({"max_payload_chars"}),
)
