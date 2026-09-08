"""Feature specification for provider-neutral model invocation."""
from app.contracts.agentic.capabilities import MANDATE_CAPABILITY,MODEL_INFERENCE_CAPABILITY,OPERATIONS_CAPABILITY,ROLES_CAPABILITY
from app.contracts.orchestration.capabilities import RESERVE_RESOURCES_CAPABILITY
from app.contracts.plugins.capabilities import REGISTER_CONTRIBUTIONS_CAPABILITY
from app.kernel.feature import FeatureSpec
SPEC:FeatureSpec=FeatureSpec(feature_id="FEAT-AGT-INVOKE_MODELS",domain="agentic",provides=frozenset({MODEL_INFERENCE_CAPABILITY}),requires=frozenset({MANDATE_CAPABILITY,OPERATIONS_CAPABILITY,ROLES_CAPABILITY,RESERVE_RESOURCES_CAPABILITY,REGISTER_CONTRIBUTIONS_CAPABILITY}),optional=frozenset(),conflicts=frozenset(),description="Invoke exact independently eligible provider/model profiles under finite budgets and strict output containment.",state=None,config_keys=frozenset({"max_payload_bytes"}))
