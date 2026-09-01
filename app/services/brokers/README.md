# Brokers — Spatial Composability & Focused Domain Architecture

> **Package:** `app/services/brokers`
> **Architecture:** Spatial Composability + Focused Domain Architecture
> **Status:** Refactored target runtime — explicit provider features + one dispatcher
> **Last updated:** 2026-09-01

Brokers is the **thin external-provider integration domain**. It owns provider
connectivity, provider-native protocol translation, provider session mechanics,
genuine provider-state reads, and transport of orders that have already been
admitted by Trading/Risk.

Brokers is deliberately **not** a second Catalogue, Composition engine, event
framework, risk/policy engine, simulation engine, or test framework.

## 1. Domain boundary

### Brokers owns

- External provider SDK/network/terminal integration.
- Exact provider account/session lifecycle.
- Verification that the configured provider environment/account matches provider
  truth at the provider boundary.
- Provider-native read normalization into Broker wire contracts.
- External mutation transport after authorization has already occurred elsewhere.
- Honest provider outcomes: `ACCEPTED`, `REJECTED`, or `UNKNOWN`.
- Provider-local reconnect/session cleanup and transport continuity.
- Provider-specific event translation before publishing through Kernel event
  infrastructure.

### Brokers does not own

| Responsibility | Owner |
| --- | --- |
| Canonical instrument identity and versions | Catalogue |
| Provider-symbol mappings / alias resolution | Catalogue |
| Sessions/calendars and canonical trading rules | Catalogue |
| Provider selection / feature discovery | Composition + Kernel |
| Secrets lifecycle and runtime admission | Workspace |
| Trade permission / risk authorization | Trading + Risk |
| Read-source fallback policy | Data |
| Durable order/deal/business reconciliation | Trading |
| Simulation execution semantics | Simulator |
| Generic typed event bus / subscription lifetime | Kernel |
| Adapter conformance certification mechanics | tests / CI |
| Release approval policy | deployment/release governance |

## 2. Public Broker capabilities

The production Broker domain exposes exactly three runtime capability bundles:

| Capability | Protocol | Responsibility |
| --- | --- | --- |
| `broker.manage-sessions@1` | `ManageSessionsCapability` | Open, reconnect, assess, transition, and close exact provider sessions. |
| `broker.read-provider-state@1` | `ReadProviderStateCapability` | Return genuine provider account/trading/market/history state. |
| `broker.transport-orders@1` | `TransportOrdersCapability` | Validate/submit/cancel/modify already-authorized provider operations and preserve `UNKNOWN`. |

There is no Broker-global `declare-capabilities`, `configure-providers`,
`isolate-environments`, or `certify-adapters` runtime capability.

Runtime availability is represented by installed providers and Kernel capability
registration. Provider selection is explicit through Composition/dispatcher
configuration. Permission is not inferred from capability presence.

## 3. Feature registry

| Feature | Package | Provides | Write transport |
| --- | --- | --- | --- |
| `FEAT-BRK-DISPATCH_PROVIDERS` | `dispatch_providers/` | all three public Broker capabilities | routes only |
| `FEAT-BRK-CONNECT_METATRADER` | `metatrader/` | `broker.provider.mt5@1` | yes, provider-local |
| `FEAT-BRK-CONNECT_CTRADER` | `ctrader/` | `broker.provider.ctrader@1` | yes, provider-local |
| `FEAT-BRK-CONNECT_BINANCE` | `binance/` | `broker.provider.binance@1` | no in current donor |
| `FEAT-BRK-CONNECT_DUKASCOPY` | `dukascopy/` | `broker.provider.dukascopy@1` | no; read-only |
| `FEAT-BRK-CONNECT_YAHOO` | `yahoo/` | `broker.provider.yahoo@1` | no; read-only |

Provider gateway capabilities are internal feature-to-feature contracts in
`app/contracts/broker/internal.py`; they are not UI/API wire surfaces.

## 4. Dispatch rule

`FEAT-BRK-DISPATCH_PROVIDERS` is the **only** feature that publishes the public
Broker runtime capabilities.

A request resolves by immutable `profile_id` / `profile_version` to exactly one
installed provider feature:

```text
caller
  ↓
broker.manage-sessions / broker.read-provider-state / broker.transport-orders
  ↓
FEAT-BRK-DISPATCH_PROVIDERS
  ↓ exact profile match; zero or >1 matches fail closed
provider gateway
  ↓
provider SDK / terminal / network
```

The dispatcher never:

- tries another provider after failure;
- resolves friendly/canonical symbols;
- grants trading permission;
- silently retries an ambiguous mutation;
- owns provider SDKs;
- persists business reconciliation state.

A `JOURNAL` request may be routed only to the provider that handled the original
operation. The dispatcher keeps only bounded runtime routing identity; Trading owns
durable reconciliation.

## 5. Provider feature rules

Every provider package follows the focused feature shape:

```text
<provider>/
  README.md
  __init__.py        # docstring only
  manifest.py        # immutable FeatureSpec
  config.py          # frozen/slotted strict configuration
  feature.py         # mount/provide/teardown glue
  gateway.py         # new Broker contract adapter
  ... donor-local provider implementation modules ...
```

Rules:

1. Provider features publish one provider-local gateway capability, never the
   three public Broker capabilities directly.
2. Provider features never import another provider feature.
3. Provider resources are disposed through `FeatureContext` / `FeatureScope`.
4. No provider defaults to `LIVE`.
5. Read-only providers cannot become writable from configuration.
6. Provider feature presence is not authorization.
7. `UNKNOWN` mutation outcomes remain `UNKNOWN`; they are never converted into a
   rejection and retried automatically.
8. Exact provider symbols are consumed as provider-native input. Broker code does
   not resolve aliases.

## 6. Environment ownership

The former standalone `environment_guards` responsibility is dissolved:

- **Workspace / Composition:** application/runtime profile and feature admission.
- **Trading / Risk:** authorization to perform a trade mutation.
- **Provider feature:** verify the requested account/environment matches the
  actual configured/provider boundary and fail closed on mismatch.

Therefore there is no `FEAT-BRK-ENVIRONMENT_GUARDS` production feature.

## 7. Capability ownership

The former global capability matrix is dissolved.

- Coarse runtime capability presence = `FeatureSpec.provides` + Kernel registry.
- Provider-specific implementation support = provider gateway behavior.
- Runtime provider selection = Composition/dispatcher.
- Instrument-specific order/TIF/quantity constraints = Catalogue.
- Trade permission = Trading/Risk.
- Conformance verification = tests/CI.
- Release approval = release/deployment governance.

A single Broker matrix must not combine those dimensions again.

## 8. Instrument and provider-symbol ownership

The former `instrument_profiles` feature is removed from Broker ownership.

Canonical flow:

```text
canonical InstrumentRef
  ↓
Catalogue provider mapping
  ↓
exact provider-native symbol
  ↓
Broker provider feature
```

Brokers may expose current provider-observed technical facts, but it does not own
canonical/versioned instrument definitions, session definitions, alias resolution,
or versioned trading constraints.

### Current v1 read-contract limitation

`ReadProviderStateRequest.READ_MARKET` currently carries an `InstrumentRef` but no
exact `provider_symbol`/timeframe. The focused Broker implementation therefore
fails that operation closed rather than performing alias resolution or hiding a
provider symbol in configuration. The wire contract must be extended before the
read can be safely represented. Yahoo and Dukascopy historical market reads are
subject to the same limitation.

## 9. Events

There is no standalone Broker event-normalization runtime feature.

- Kernel owns event-bus mechanics and subscription cleanup.
- `app/contracts/broker/events.py` owns Broker event semantics.
- Provider features translate provider callbacks into Broker event payloads and
  publish through `FeatureContext` when the provider stream is enabled.
- Data owns durable market-feed processing checkpoints.
- Trading owns durable execution/order/deal reconciliation checkpoints.
- A provider may retain only transport-local continuation state required by the
  provider protocol.

The legacy `NORMALIZE_EVENT` read operation is retained only for wire compatibility
and fails `CAPABILITY_UNAVAILABLE`; it is not a new runtime responsibility.

## 10. Simulation

Simulation is not an external broker.

`Simulator` owns simulated fills/execution behavior. Trading chooses the execution
route by capability. Broker must not require Simulator to impersonate an external
provider.

The legacy Broker `simulation/` adapter is therefore a migration/deletion target,
not a target Broker feature.

## 11. Conformance and certification

Provider contract tests remain important, but they are test/CI mechanics.

- Fakes/fixtures/conformance suites live under `tests/services/brokers/`.
- Runtime provider features do not publish `broker.certify-adapters@1`.
- Certification/release evidence may be produced by CI without becoming a
  production service capability.

## 12. State ownership

| State | Owner | Persistence |
| --- | --- | --- |
| Provider socket/terminal/session handles | provider feature | ephemeral |
| Provider reconnect/subscription mechanics | provider feature | ephemeral / provider-local if required |
| Dispatch profile-to-provider resolution | dispatcher / Composition | configuration/runtime |
| Canonical instrument/provider mappings | Catalogue | Catalogue-owned retained state |
| Trade authorization | Trading/Risk | owner-defined |
| Order/deal reconciliation | Trading | Trading-owned retained state |
| Market-feed processing checkpoints | Data | Data-owned retained state |
| Conformance evidence | tests/CI | CI artifacts |

No global Brokers database is part of the target architecture.

## 13. Removal map from the legacy Broker domain

| Legacy area | Disposition |
| --- | --- |
| `instrument_profiles/` | move responsibility to Catalogue; remove from Brokers |
| `capabilities/` | dissolve into FeatureSpec/provider behavior/Catalogue/Trading/tests |
| `environment_guards/` | dissolve into Workspace/Composition + Trading/Risk + provider verification |
| `events/` | Kernel event infrastructure + Broker event contracts + consumer-owned checkpoints |
| `reconciliation/` | provider reconnect local; Data read policy; Trading business reconciliation |
| `simulation/` | Simulator/Trading |
| `conformance/` | tests/CI |
| `specifications/` | current provider facts only where needed; canonical/versioned rules Catalogue |
| global `persistence/` + `migrations/` | delete after legacy consumers are migrated |
| `_shared/` + `canonical_contracts/` | brownfield donor compatibility only; eliminate after provider-local migration |
| package-root service locator/factory facade | replace with feature discovery + capabilities |

## 14. Safety invariants

- No provider mutation occurs without a `BrokerOperationRequest` carrying
  `risk_authorization_id`, explicit provider symbol, normalized quantity, request
  hash, and idempotency key.
- The Broker domain never chooses a safer/different provider on behalf of the
  caller.
- A transport timeout after possible submission is `UNKNOWN`, never an assumed
  rejection.
- Live is never the default environment.
- Read-only providers remain structurally read-only.
- Provider credentials are process-local resolved values; wire contracts expose
  only Workspace `SecretRef` identities. Secrets never enter Broker events,
  diagnostics, or public records.

## 15. Verification

Focused architecture evidence lives under `tests/services/brokers/` and must cover:

- exact profile dispatch;
- zero/duplicate provider route failure;
- provider environment mismatch;
- read-only mutation rejection;
- provider teardown/removability;
- unknown mutation preservation;
- manifest capability ownership;
- no provider-to-provider implementation imports;
- removal of obsolete runtime capabilities;
- safe behavior when an optional provider SDK is unavailable.

Run the repository quality gates after migration:

```bash
uv run --frozen ruff format --check app tests
uv run --frozen ruff check app tests
uv run --frozen mypy
uv run --frozen pytest
```

The domain refactor is complete only when target provider features are discoverable,
legacy consumers no longer depend on the Broker package-root service locator, and
obsolete Broker-owned runtime features can be deleted without changing application
behavior.
