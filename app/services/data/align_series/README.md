# FEAT-DATA-ALIGN_SERIES — Align Series

## Purpose

Validate point-in-time alignment policies and materialize immutable exact-alignment versions without permitting future observations to affect earlier decisions.

## Domain

data

## Provides

- `data.align-series@1`

## Required Capabilities

- `data.series-store@1`

## Optional Capabilities

None.

## Configuration

None.

## Runtime Effects

Policy validation is read-only. `ALIGN` reads one immutable source version and writes one immutable aligned version through the declared series-store capability. Mount performs no I/O.

## Persistent State

None. Materialized aligned versions are retained by `FEAT-DATA-MANAGE_SERIES`.

## Functional Requirements

- Require `look_ahead_prohibited=true` through the public contract.
- Preserve source content exactly for `EXACT` alignment while allocating a new immutable version identity.
- Never synthesize target timestamps that are absent from the request.
- Fail `LAST_KNOWN` and `AGGREGATE` closed under v1 because their age/missingness semantics require an explicit target timeline.

## Failure Behavior

Unknown source versions fail `DATA_NOT_FOUND`. Alignment modes that cannot be proven from v1 inputs fail `DATA_ALIGNMENT_INCOMPATIBLE`; no fallback or invented data is produced.

## Removal Behavior

Removing this feature withdraws `data.align-series@1`; source and previously materialized aligned versions remain owned by the immutable series store.
