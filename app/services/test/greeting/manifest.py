"""Feature specification manifest for test greeting."""

from app.contracts.test.greeting import GREETING_SERVICE
from app.kernel.feature import FeatureSpec

SPEC = FeatureSpec(
    feature_id="FEAT-TEST-GREETING",
    domain="test",
    provides=frozenset({GREETING_SERVICE}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Provide deterministic greeting generation for validated caller names",
    config_keys=frozenset({"default_salutation", "max_name_length"}),
    state=None,
)
