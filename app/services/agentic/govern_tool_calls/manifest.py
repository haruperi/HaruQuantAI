"""Feature specification for Agentic tool governance."""

from app.contracts.agentic.capabilities import MANDATE_CAPABILITY, OPERATIONS_CAPABILITY, ROLES_CAPABILITY, TOOL_GOVERNANCE_CAPABILITY
from app.contracts.orchestration.capabilities import RESERVE_RESOURCES_CAPABILITY
from app.contracts.workspace.capabilities import MANAGE_ACCOUNTS_CAPABILITY, PERSISTENCE_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
 feature_id="FEAT-AGT-GOVERN_TOOL_CALLS", domain="agentic", provides=frozenset({TOOL_GOVERNANCE_CAPABILITY}),
 requires=frozenset({MANDATE_CAPABILITY, OPERATIONS_CAPABILITY, ROLES_CAPABILITY, MANAGE_ACCOUNTS_CAPABILITY, PERSISTENCE_CAPABILITY, RESERVE_RESOURCES_CAPABILITY}),
 optional=frozenset(), conflicts=frozenset(), description="Issue invocation-bound tool leases, reauthorize calls, contain results, and bind human actions.",
 state=StateDeclaration(namespace="agentic.tool_governance", schema_version=1, retention_policy=RetentionPolicy.RETAIN, description="Tool leases, nonce use, and typed human decisions."),
 config_keys=frozenset({"max_result_bytes"}),
)
