# Observe Market Catalogue — FEAT-IFACE-OBSERVE_MARKET_CATALOGUE

> Runtime-validated feature specification. `scripts/validate_feature_docs.py`
> checks this document against `manifest.py` on every run. The domain-level
> registry lives in `app/services/interfaces/README.md`.

## Purpose

Expose the market catalogue browse surface for the Markets widget
migration: project the Catalogue-owned instrument catalogue
(`catalogue.catalog-instruments@1`) into bounded browse pages carrying
identity, asset class, and precision, with continuation cursors and
page-level revision identity. Live price fields stay null — the catalogue
owns no market prices and none are invented; price enrichment belongs to
the observation stream. The gateway never imports a Catalogue
implementation and reports absence truthfully through the stable
`CAPABILITY_UNAVAILABLE` failure.

## Domain

interfaces

## Provides

| Capability bundle | Runtime identifier |
| --- | --- |
| ObserveMarketCatalogueCapability | `interfaces.observe-market-catalogue@1` |

## Required Capabilities

| Capability bundle | Runtime identifier |
| --- | --- |
| CatalogInstrumentsCapability | `catalogue.catalog-instruments@1` |

## Optional Capabilities

None.

## Configuration

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `default_page_size` | integer 1..500 | `100` | Page size applied when a request omits one. |
| `max_page_size` | integer 1..500 | `200` | Upper bound applied to every requested page size. |

Unknown keys are rejected with `ValueError`.

## Runtime Effects

- Resolves the required `catalogue.catalog-instruments@1` provider
  through `FeatureContext`; absence fails the mount closed (`BLOCKED`).
- Runs no background tasks and holds no buffers: each request projects
  one bounded provider page.
- Registers exactly one scope cleanup callback (`gateway.close`) so
  later use fails closed; repeated disposal is safe.

## Persistent State

None. Catalogue truth and versioning remain owned by the Catalogue
domain.

## Functional Requirements

| Requirement | Requirement statement | Usage-harness scenario |
| --- | --- | --- |
| FR-IFACE-OMC-001 | Project bounded catalogue pages with continuation cursors. | page projection |
| FR-IFACE-OMC-002 | Clamp requested page sizes to the configured maximum. | page-size clamp |
| FR-IFACE-OMC-003 | Carry page-level revision identity and a projection timestamp. | revision identity |
| FR-IFACE-OMC-004 | Keep live price fields null; never invent market data. | null prices |
| FR-IFACE-OMC-005 | Fail closed with CAPABILITY_UNAVAILABLE after disposal. | disposal failure |

Run the bounded executable demonstration with:

```powershell
uv run python -m app.services.interfaces.observe_market_catalogue.gateway
```

## Failure Behavior

- Missing `catalogue.catalog-instruments@1` provider blocks activation
  (`CapabilityUnavailableError` during mount); the feature provides
  nothing.
- Provider failures map to the stable `CAPABILITY_UNAVAILABLE`
  interface failure carrying the provider's detail.
- Use after disposal returns `CAPABILITY_UNAVAILABLE`; repeated disposal
  is a no-op.

## Removal Behavior

Disabling or removing the feature withdraws exactly the
`interfaces.observe-market-catalogue@1` capability: Python consumers
receive `CapabilityUnavailableError` and the served routes translate it
to the stable 503 `CAPABILITY_UNAVAILABLE` envelope. The Catalogue
provider and its data are unaffected; unrelated Interfaces features
remain active.
