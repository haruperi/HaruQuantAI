"""Capability declaration for the Portfolio gateway.

This module carries data only and imports nothing from the capability it
describes, so composition can read the declaration without loading the feature.
Deleting the capability deletes this declaration with it, which is how the
composition layer learns the capability is absent.
"""

CAPABILITY_ID = "portfolio"

# Import packages this capability owns. A missing module under one of these
# prefixes means the capability itself is absent rather than broken.
PACKAGES = (
    "app.services.api.widgets.portfolio",
    "app.services.portfolio",
)

# Capability identifiers this one cannot operate without. An unsatisfied
# requirement deactivates this capability instead of failing startup.
REQUIRES = ("analytics",)
