"""Feature specification for settings and diagnostic translation."""
from app.contracts.interfaces.capabilities import OPERATE_SETTINGS_CAPABILITY
from app.contracts.workspace.capabilities import ADMINISTER_SETTINGS_CAPABILITY,BUILD_DIAGNOSTICS_CAPABILITY
from app.kernel.feature import FeatureSpec
SPEC:FeatureSpec=FeatureSpec(feature_id="FEAT-IFACE-OPERATE_SETTINGS",domain="interfaces",provides=frozenset({OPERATE_SETTINGS_CAPABILITY}),requires=frozenset({ADMINISTER_SETTINGS_CAPABILITY,BUILD_DIAGNOSTICS_CAPABILITY}),optional=frozenset(),conflicts=frozenset(),description="Translate versioned settings plus bounded diagnostics without acquiring semantic ownership.",state=None,config_keys=frozenset())
