# FEAT-DATA-NORMALIZE_TICKS — Normalize Ticks

## Purpose
Normalize validated raw tick batches into deterministic immutable Data evidence while preserving genuine provider fields and explicit ordering findings.

## Domain
data

## Provides
- `data.normalize-ticks@1`

## Required Capabilities
- `data.series-store@1`

## Optional Capabilities
None.

## Configuration
None.

## Runtime Effects
Each request performs bounded in-memory ordering/hash work and one immutable write through the required series-store capability. Mount itself performs no I/O and owns no background task.

## Persistent State
None. Durable normalized payloads are owned by `FEAT-DATA-MANAGE_SERIES` through `data.series-store@1`.

## Functional Requirements
- Preserve bid, ask, last, volume, flags, timestamps, and source sequence exactly.
- Order by timestamp then source sequence without forward inference.
- Surface reordered and duplicate-key evidence explicitly.
- Publish one immutable UUIDv7 version and canonical SHA-256 payload hash.

## Failure Behavior
Invalid public tick records are rejected by the Data contracts before invocation. Missing series-store dependency blocks activation. Store conflicts or persistence failures propagate and no false success is returned.

## Removal Behavior
Removing the feature withdraws `data.normalize-ticks@1`; stored versions remain retained by their owning series-store feature and unrelated Data capabilities remain active.
