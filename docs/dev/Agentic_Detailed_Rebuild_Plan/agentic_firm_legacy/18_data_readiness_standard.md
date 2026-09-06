# Agentic Data Readiness Standard

> **Status:** Active supporting specification
>
> **Canonical requirements:** `FR-AGENTIC-016`, `022`–`036`;
> `NFR-AGENTIC-006`

## Activation rule

An evidence-dependent role remains disabled until its upstream owner exposes a
governed public contract satisfying this standard. Agentic never acquires missing
data itself or asks a model to substitute general knowledge.

## Universal fields

- Source/provider and license/usage policy
- Instrument, issuer, venue, asset class, region, and language scope
- Event/effective, published, first-seen, available, revised, and retrieved UTC times
- Original and normalized content hashes
- Revision/version chain and deduplication identity
- Quality, completeness, source-trust, and manipulation indicators
- Corporate-action, symbol, currency, and timezone lineage where applicable
- Sensitivity, retention, deletion, and training-use policy
- Injection/poisoning classification

## Capability prerequisites

| Capability | Required governed evidence |
|---|---|
| Fundamental | filings, financial statements, earnings/transcripts, issuer actions, macro data |
| Sentiment | licensed news and approved social/alternative sources with revisions and trust |
| Technical | canonical market data, sessions, indicator versions, quality and availability |
| Quantitative | Research/Analytics datasets, estimators, sample lineage, splits, leakage evidence |
| Trader/thesis | supporting analyst packs plus deterministic market, strategy, and risk context |
| Portfolio/risk advisory | current allocation, analytics, mandate, risk, account, and correlation evidence |

## Point-in-time rule

Every record is selected by what was available to the system at the decision time,
not by its final revised value. Later corrections remain separate versions.
Unknown availability time makes evidence ineligible for historical evaluation.

## Source disagreement

Conflicting sources are preserved with trust and availability evidence. The system
does not silently choose, average, or rewrite them. Material unresolved conflict is
reported to deliberation and may require refusal.
