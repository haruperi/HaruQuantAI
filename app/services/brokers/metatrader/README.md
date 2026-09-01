# FEAT-BRK-CONNECT_METATRADER — MetaTrader Provider

Own one removable MetaTrader terminal/account integration. The feature verifies the
configured provider environment/account at the session boundary, performs genuine
provider reads, and transports already-authorized orders. It does not resolve
instrument aliases, select providers, authorize risk, or reconcile business outcomes.

## Provides

`broker.provider.mt5@1` (internal Broker gateway).

## Configuration

`profile_id`, `profile_version_id`, `profile_version`, `account_ref`, explicit
`environment` (`LIVE` or `DEMO`), process-local resolved `credentials`, optional
`probe_symbol`, and bounded connection/request timeouts. There is no default to live.

## Removal

Unmounting the feature disconnects the owned terminal through `FeatureContext`
teardown. Removing this package removes MT5 behavior without changing the dispatcher
or another provider feature.
