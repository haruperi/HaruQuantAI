"""Executable real-market event evidence example for Strategy hosts."""

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import get_market_data
from app.services.data.contracts import DataError
from app.services.strategy import StrategyEvent
from app.utils import canonical_json

print("\nREAL BAR-CLOSED STRATEGY EVENT")
print("=" * 88)
try:
    market = get_market_data(
        source_id="mt5",
        symbol="EURUSD",
        timeframe="M5",
        limit=2,
        use_cache=False,
    )
except DataError as error:
    print("Live MT5 data unavailable:", error.code)
    sys.exit(3)

bar = market.records[-1]
source_checksum = hashlib.sha256(
    canonical_json(market.model_dump(mode="json")).encode()
).hexdigest()
event = StrategyEvent(
    event_type="BAR_CLOSED",
    hook="on_bar",
    occurred_at=bar.timestamp,
    sequence=market.record_count - 1,
    source_owner="data",
    source_contract_version=market.contract_version,
    source_schema_id=market.schema_id,
    source_snapshot_ref=market.request_id,
    source_checksum=source_checksum,
    source_as_of=bar.timestamp,
    facts={"symbol": market.symbol, "timeframe": market.timeframe or ""},
    request_id=market.request_id,
    workflow_id="strategy-usage-event-workflow",
    correlation_id="strategy-usage-event-correlation",
)
print("Event:", event.event_type, event.hook)
print("Occurred at:", event.occurred_at)
print("Source dataset:", event.source_snapshot_ref)
print("Close:", bar.close)
