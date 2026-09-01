# FEAT-DATA-PREPARE_PROFILES — Prepare Profiles

## Purpose
Validate whether immutable Data evidence has sufficient precision for downstream volume/TPO profile calculations without calculating those profiles inside Data.

## Domain
data

## Provides
- `data.prepare-profiles@1`

## Required Capabilities
- `data.series-store@1`

## Optional Capabilities
None.

## Configuration
None.

## Runtime Effects
Each request performs one bounded series-store metadata read. The feature owns no file, socket, task, or database state.

## Persistent State
None. The source Data version is retained by the series-store owner.

## Functional Requirements
- Require a committed stored Data version.
- Require tick-shaped evidence for `TICK` profile sources.
- Require bar/scenario evidence for `LOWER_GRANULARITY` sources.
- Return explicit diagnostics when precision is insufficient.
- Never calculate a volume/TPO profile or invent missing volume.

## Failure Behavior
Unknown versions return `DATA_NOT_FOUND`; missing `data.series-store@1` blocks activation. Precision insufficiency is represented in the successful source evidence with `is_sufficient=false`, not hidden.

## Removal Behavior
Removing the feature withdraws `data.prepare-profiles@1` only; source series and downstream calculation implementations remain unaffected.
