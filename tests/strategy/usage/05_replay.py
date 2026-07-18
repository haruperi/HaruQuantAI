"""Executable overview of Strategy replay contracts."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.strategy import (
    StrategyCheckpoint,
    StrategyReplayManifest,
)

print("\nSTRATEGY REPLAY CONTRACTS")
print("=" * 88)
print(
    "Replay schema:",
    StrategyReplayManifest.model_json_schema()["properties"]["schema_id"]["default"],
)
print(
    "Checkpoint schema:",
    StrategyCheckpoint.model_json_schema()["properties"]["schema_id"]["default"],
)
print("Replay creation requires a real validated registry/configuration pair.")
print("Checkpoint creation additionally persists through the configured Data store.")
