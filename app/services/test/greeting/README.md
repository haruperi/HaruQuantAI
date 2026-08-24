# Test Greeting Feature Specification

> **Feature ID:** `FEAT-TEST-GREETING`
> **Domain:** `test`
> **Capability:** `test.greeting@1`
> **Status:** `Implemented`

## Purpose

Provide deterministic greeting message generation with caller-name validation and configurable salutation for the temporary test domain.

## Domain

`test`

## Provides

- `test.greeting@1`

## Required Capabilities

None

## Optional Capabilities

None

## Configuration

| Key | Type | Default | Description |
|---|---|---|---|
| `default_salutation` | string | `"Hello"` | Default salutation prefix used when not explicitly specified in request. |
| `max_name_length` | integer | `100` | Maximum permitted character length for caller names. |

## Runtime Effects

- Staged capability provider `test.greeting@1` published to the service registry during mount.
- Capability provider withdrawn and revoked cleanly upon feature scope disposal.

## Persistent State

None

## Functional Requirements

- `FR-TEST-GENERATE_GREETING`: Validate caller name (non-empty, trimmed, bounded length) and return formatted greeting `f"{salutation}, {name}!"`.

## Failure Behavior

- Raises `ValueError` when caller name is empty, whitespace-only, or exceeds `max_name_length`.
- Invalid configuration keys or non-positive `max_name_length` raise `ValueError` during configuration parsing.

## Removal Behavior

- Physical deletion of this feature package cleanly removes `test.greeting@1` without impacting kernel or unrelated domains.
