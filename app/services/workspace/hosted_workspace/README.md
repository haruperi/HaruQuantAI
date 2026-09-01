# Hosted Workspace Boundary

> **Feature ID:** `FEAT-WS-HOST_WORKSPACES`
> **Status:** `Implemented`

## Domain

`workspace`

## Provides

- `workspace.host-workspaces@1`

## Required Capabilities

None

## Optional Capabilities

None

## Configuration

None

## Purpose

Isolate hosted workspaces and authorize principals.

## Runtime Effects

- Manages in-memory registration and lookup of isolated hosted workspace contexts.
- Enforces cross-workspace uniqueness on all six isolation scopes (`metadata_scope`, `artifact_scope`, `queue_scope`, `credential_scope`, `quota_scope`, `plugin_permission_scope`).
- Evaluates authenticated principal authorization rules and returns fail-closed decisions.

## Failure Behavior

- Scope collisions across distinct hosted workspaces return `ISOLATION_CONFLICT` failure.
- Describing unprovisioned workspaces returns `WORKSPACE_NOT_FOUND` failure.
- Missing evidence or policy uncertainty during authorization yields typed `DENY` decision with non-empty reason.

## Removal Behavior

Removing `hosted_workspace` makes hosted workspace provisioning and authorization unavailable (`CAPABILITY_UNAVAILABLE`). Local workspace mode remains unaffected.

## Persistent State

None
