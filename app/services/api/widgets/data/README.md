# Data Gateway

Focused workstation API feature. It authenticates and authorizes requests,
delegates through verified owner-domain public contracts, translates bounded
errors, and performs no owner-domain or presentation calculations.

For live MT5 presentation it exposes authenticated single-symbol and
multi-symbol SSE transports over Data-owned one-second TCP snapshots. Broker
source identity is preserved in every snapshot payload alongside sequence, gap,
freshness, and quote evidence. Brokers owns socket acquisition; Data owns symbol filtering, canonical mapping,
sequencing, and stale evidence.

## Files

- `routes.py`: thin FastAPI transport boundary.
- `schemas.py`: feature-local request and response schemas.
- `orchestration.py`: dependency composition and owner delegation.
- `stream_routes.py`: quota-bound SSE transport for TCP-originated live quotes.

Additional focused route or persistence modules are listed here when required by
the feature's distinct resource lifecycle.

## Requirements

- FR-API-024, FR-API-033, FR-API-119, and FR-API-127.

## Bar history

`GET /api/v1/data/bars` is the Chart widget's only source of price history.
It resolves the configured runtime broker, delegates one bounded
`get_market_data` read to Data, and projects the returned OHLCV records as
JSON numbers with ISO-8601 UTC bar-open instants.

Three properties are deliberate:

- **The timeframe domain is closed.** `schemas.BarTimeframe` restates Data's
  canonical manifest, so a key the broker has no bars for is refused with 422
  at the boundary rather than surfacing as an `UNSUPPORTED_TIMEFRAME` failure.
- **Bars are read uncached.** A chart's newest bar changes on every tick; a
  cached window would render as a frozen market.
- **An unavailable series stays unavailable.** MT5 can return only its current
  bar while synchronizing a symbol, which triggers exactly one retry. Beyond
  that, an empty or failed provider read is returned as an error or empty
  envelope. The gateway never substitutes generated prices, because a chart
  cannot distinguish invented history from real history.

## Dependencies

Shared API contracts, Identity authorization, canonical Composition, and the
relevant owner-domain package-root public API.

## Evidence

- `tests/api/unit/test_data_routes.py and test_data_stream_route.py`
