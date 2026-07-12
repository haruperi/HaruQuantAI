# ADR-0008: Persistence Infrastructure and Schema Ownership

**Status:** Accepted
**Date:** 2026-07-12
**Deciders:** Haruperi (Owner)
**Source:** PROJECT.md OD-8

## Context

Six domains persist state (Data, Trading, Simulation, Optimization, Research; Analytics potentially). SQLite is the shared store, which forces care around connections, write locking, and migrations. Two extremes were on the table: fully centralized persistence (Data owns all tables) or fully decentralized (each domain runs its own database machinery).

## Decision

Split infrastructure from schema. Data owns the shared database connection, locking, and migration execution framework. Each persistent domain owns its own tables, artifact schemas, and migration definitions, executed through Data's framework. Analytics remains read-only and does not persist reports in the initial build.

## Options Considered

### Option A: Data owns all tables and schemas

**Pros:** One persistence authority; no schema drift.
**Cons:** Data would encode Trading's order semantics, Simulation's journals, Research's artifacts — every domain change becomes a Data change; violates one-responsibility-one-owner.

### Option B: Each domain owns its own database machinery

**Pros:** Full autonomy.
**Cons:** Multiple SQLite connection/locking implementations against the same file is exactly how corruption and `database is locked` bugs happen; duplicated migration tooling.

### Option C: Shared infrastructure in Data, schemas in owning domains (chosen)

**Pros:** Single implementation of the dangerous parts (connections, exclusive path-scoped write locks, migration execution); domain knowledge stays with its owner; data-ownership table (Section 5) falls out naturally — only the owner writes its tables.
**Cons:** Migration ordering across domains needs coordination through the shared framework; Data's framework becomes a critical dependency for all persistent domains.

## Trade-off Analysis

SQLite's single-writer reality demands centralized locking; domain autonomy demands decentralized schemas. Option C takes each where it matters. Keeping Analytics read-only initially avoids prematurely designing report persistence before real reporting needs exist.

## Consequences

- One connection/locking/migration implementation; `CONCURRENT_WRITE_LOCKED` is the single conflict surface.
- Each persistent domain's README documents its tables and migrations; Data's README documents the framework.
- The Section 5 data-ownership table is the authoritative map of who writes what.
- If Analytics later needs persisted reports, that is a schema addition under Analytics ownership — no infrastructure change.

## Action Items

1. [ ] Define the migration execution framework contract in the Data README.
2. [ ] Add a dependency-audit check that no domain opens its own SQLite connection.
