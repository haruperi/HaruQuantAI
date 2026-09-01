# FEAT-BRK-CONNECT_METATRADER MetaTrader Direct Broker Channel

This folder is the sole production owner of `FEAT-BRK-CONNECT_METATRADER`, publishing strictly the `broker.provider.metatrader@1` (`PROVIDER_METATRADER_CAPABILITY`) provider backend capability.

## Overview

MetaTrader 5 provider feature providing genuine terminal connection lifecycle, account state reads, market data, Depth-of-Market reads, revisioned snapshot symbol demand, and authorized demo mutations.

## Architecture

- `manifest.py`: Immutable `FeatureSpec` declaring `broker.provider.metatrader@1` and strict configuration keys.
- `config.py`: Frozen dataclass `MetaTraderConfig` with immutable configuration defaults.
- `metatrader.py`: Domain service `MetaTraderProviderService` implementing `ProviderBackend` protocol (`manage_sessions`, `read_provider_state`, `transport_orders`, `close`) and executable usage demonstration harness.
- `feature.py`: Wiring-only feature `MetaTraderFeature` (`mount`/`unmount` lifecycle) and `feature()` entry point.
- `mapping.py`: Provider normalization mappers to canonical contracts and wire record structures.
- `transport.py`: Serialized non-blocking MT5 terminal transport boundary.
- `commands.py`, `snapshots.py`, `calculations.py`: Private provider mixins for mutations, execution history, and margin/profit calculations.
- `snapshot_gateway.py`, `snapshot_protocol.py`: Multi-consumer revisioned symbol demand and Depth-of-Market protocol over authenticated control connections.

## Mutation Policy

- Mutations in `DEMO` environment are permitted for verified demo sessions.
- Unreleased operations fail with `BROKER_PROFILE_UNSUPPORTED`.
- Live operations fail closed by default with `BROKER_LIVE_TRADING_DENIED` unless authorized upstream by Trading/Risk.
- Uncertain mutation outcomes return `BROKER_UNKNOWN_MUTATION_OUTCOME` without automatic retry.
