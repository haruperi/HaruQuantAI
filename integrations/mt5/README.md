# HaruQuantAI MT5 Snapshot Bridge

The tested `TickBridge.mq5` publishes one read-only, multi-symbol
quote snapshot and one read-only, multi-symbol Depth-of-Market (DOM) book per
second to HaruQuantAI's local TCP receiver. It does not accept orders,
credentials, or account mutations.

## Install

1. Compile the tested EA with MetaEditor and attach it to one chart.
2. Allow socket access to `127.0.0.1` in MT5's Expert Advisor settings.
3. Configure identical shared-token values in the EA and the backend's
   `HARUQUANT_MT5_SHARED_TOKEN` environment variable.
4. Start the HaruQuantAI API. The default receiver is `127.0.0.1:9001`.

The listener host and port can be overridden with
`HARUQUANT_MT5_SNAPSHOT_HOST` and `HARUQUANT_MT5_SNAPSHOT_PORT`. External
binding is not recommended without network-level access controls.

## Protocol

Each UTF-8 JSON object is terminated by `\n`. The connection starts with the
authenticated `haruquant.mt5.snapshot.v2` hello. HaruQuantAI then sends
revisioned complete `set_symbols` commands; the EA selects valid broker-native
symbols and replies with `symbols_applied` plus explicit per-symbol errors before
publishing snapshots for that acknowledged revision. Watchlist changes therefore
update the active EA set without recompilation or streaming the full catalogue.
An acknowledged empty set pauses `SymbolInfoTick` reads and snapshot payloads;
the EA sends only a three-second revision heartbeat to retain control-channel
health. A later acknowledged non-empty set resumes snapshots automatically.
Quotes preserve Bid, Ask, Last, volume, broker millisecond time, flags, and
digits. Frames are limited to 1 MiB. Malformed, oversized, duplicate, and
out-of-order frames are rejected or ignored explicitly. The shared token is
never included in API responses or logs.

`InpSymbols` is used only to declare a bootstrap fallback during connection.
`InpAuthToken` intentionally has no source-code default: paste the same rotated
token configured in HaruQuantAI into the EA Inputs dialog. Update the backend and
EA together because protocol v1 and v2 are intentionally incompatible.

## Depth-of-Market (book) frames

Immediately after each snapshot, the EA sends one `book` frame carrying every
acknowledged symbol's current Depth-of-Market read, using its own independent
sequence counter. For each symbol the EA calls `MarketBookAdd` once when the
symbol is applied (and `MarketBookRelease` once when it is dropped or on
`OnDeinit`), then reads `MarketBookGet` once per timer tick — the MT5 Python
and MQL5 APIs are pull-based here, not event-driven, so this bridge polls at
the same one-second cadence as quotes rather than reacting to `OnBookEvent`.

Not every broker or symbol publishes a book. A symbol whose `MarketBookAdd`
failed is reported in the frame's `errors` array (`code: 0`), never as a
synthesized empty book; a subscribed symbol with zero current resting orders
is reported as a genuine empty book (`bids: []`, `asks: []`). Each symbol
entry also carries `book_depth`, the broker's own `SYMBOL_TICKS_BOOKDEPTH`
value — `0` means this broker does not publish a queue for that symbol at
all, and callers should treat depth as permanently unavailable for it rather
than retrying. Levels are bounded to 50 per side. Only `BOOK_TYPE_BUY` and
`BOOK_TYPE_SELL` price levels are reported; broker-published market-order
queue volume (`BOOK_TYPE_BUY_MARKET`/`BOOK_TYPE_SELL_MARKET`) has no price
level to attach to and is not currently modeled.

Forex/CFD Depth-of-Market is broker-local, not a global order book — it
reflects only the liquidity this broker chooses to publish, which may be its
own client flow, an aggregated liquidity-provider feed, or nothing at all.
Present it to end users as "Broker DOM," not as a global market order book.
