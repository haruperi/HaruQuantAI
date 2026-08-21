"""Feature specification for Persistent Storage."""

from app.contracts.system.storage import SYSTEM_STORAGE
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC = FeatureSpec(
    feature_id="FEAT-SYS-PERSIST_STORAGE",
    domain="system",
    provides=frozenset({SYSTEM_STORAGE}),
    description="Durable disk-backed partitioned key-value storage engine",
    state=StateDeclaration(
        namespace="system.storage",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description="Root persistent key-value and partition data files",
    ),
    config_keys=frozenset({"driver", "db_path", "base_path"}),
)
