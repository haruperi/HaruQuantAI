# Unified CLI and MCP Automation

> **Feature ID:** `FEAT-IFACE-AUTOMATE_COMMANDS`
> **Status:** `Implemented`

## Domain

`interfaces`

## Provides

- `interfaces.automate-commands@1`

## Required Capabilities

None

## Optional Capabilities

None

## Configuration

| Setting | Type | Default | Description |
|---|---|---|---|
| `title` | string | `HaruQuantAI Automation Gateway` | Gateway title descriptor |
| `command_timeout_seconds` | number | `30.0` | Default timeout for synchronous commands |
| `max_durable_jobs` | integer | `1000` | Maximum retained durable jobs in memory |
| `enable_mcp` | boolean | `true` | Flag indicating if MCP endpoints are enabled |

## Purpose

Wrap application services through cli/mcp and portable manifests.

## Runtime Effects

- Exposes standard application command execution and parameter normalization across UI, CLI, and MCP callers.
- Enforces consistent validation, error formatting, and result schemas regardless of invocation channel.
- Tracks long-running durable operations, lifecycle status, progress updates, and cooperative cancellation requests.
- Retains background jobs independently of client disconnection until completion or explicit cancellation.

## Failure Behavior

- If a command name is empty or unregistered, an `ApplicationCommandResult` with `VALIDATION_FAILED` is returned.
- If a command payload fails schema validation, structured validation error messages are returned.
- If an unhandled exception occurs in a command handler, `EXECUTION_FAILED` is returned.
- If a requested durable job ID is not found, `DurableJobNotFoundError` (`DURABLE_JOB_NOT_FOUND`) is raised.

## Removal Behavior

Removing `cli_mcp_automation` withdraws CLI and MCP automation capabilities (`CAPABILITY_UNAVAILABLE`). HTTP/SSE API endpoints and core application domain services remain operable.

## Persistent State

None

## Functional Requirements

- `FR-IFACE-DELEGATE_APPLICATION_CALLS`: UI and CLI shall call the same application commands and queries and receive the same validation/error codes.
- `FR-IFACE-TRACK_DURABLE_COMMANDS`: Every long-running CLI/MCP operation shall return a durable job/run reference and support status, wait/follow, stop/cancel, and reconnect.
