"""Feature specification for finite resource admission and ledger management."""

from app.contracts.orchestration.capabilities import RESERVE_RESOURCES_CAPABILITY
from app.contracts.workspace.capabilities import (
    ADMINISTER_SETTINGS_CAPABILITY,
    PERSISTENCE_CAPABILITY,
)
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC = FeatureSpec(
    feature_id="FEAT-ORCH-RESERVE_RESOURCES",
    domain="orchestration",
    provides=frozenset({RESERVE_RESOURCES_CAPABILITY}),
    requires=frozenset({PERSISTENCE_CAPABILITY}),
    optional=frozenset({ADMINISTER_SETTINGS_CAPABILITY}),
    description=(
        "Admit finite hierarchical work under one authoritative resource ledger."
    ),
    state=StateDeclaration(
        namespace="orchestration.reserve_resources",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description=(
            "Hierarchical resource profiles, admission leases, "
            "and ledger audit receipts."
        ),
    ),
    config_keys=frozenset(),
)
