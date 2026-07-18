"""Executable read-only view of the configured Strategy registry."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.strategy import list_strategy_versions

print("\nCONFIGURED STRATEGY REGISTRY")
print("=" * 88)

if os.getenv("RUN_STRATEGY_STATEFUL_USAGE") != "1":
    print("Set RUN_STRATEGY_STATEFUL_USAGE=1 to open the configured Strategy store.")
    sys.exit(3)

outcome = list_strategy_versions()
print("Status:", outcome.status)
if outcome.data is not None:
    if not outcome.data:
        print("No immutable strategy versions are registered in the configured store.")
    for reference in outcome.data:
        manifest = reference.manifest
        print(
            manifest.strategy_id,
            manifest.strategy_version,
            reference.lifecycle_status.value,
            manifest.module_path,
        )
elif outcome.error is not None:
    print("Registry unavailable:", outcome.error.code, outcome.error.message)
