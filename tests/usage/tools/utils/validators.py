from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.utils import validate_approval_packet, validate_blocked_actions

request_id = "usage-utils-validator-001"
approval = validate_approval_packet(
    packet={
        "request_id": request_id,
        "action": "run_backtest",
        "risk_level": "medium",
        "requested_by": "strategy_designer",
        "evidence": [{"type": "strategy_spec", "id": "spec-001"}],
    },
    request_id=request_id,
)
blocked = validate_blocked_actions(
    attempted_actions=["read_data", "place_order"],
    blocked_actions=["place_order", "close_position"],
    request_id=request_id,
)
print(approval["status"], approval["data"])
print(blocked["status"], blocked["data"])
