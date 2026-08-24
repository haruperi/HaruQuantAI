# FEAT-UI-COMPOSE_SHELL: Compose Shell

## Purpose

Assemble a capability-aware client shell without import-order coupling or static service dependencies. The shell composes the header, workspace navigation switcher, active workspace outlet, global capability/system status bar, and footer based on the live capability snapshot from the UI composition bridge.

## Requirements Implemented

| Requirement ID | Responsibility | Acceptance / Evidence |
| --- | --- | --- |
| `FR-UI-ASSEMBLE_SHELL` | Compose header, navigation, workspace outlet, global status, and optional footer from the active capability snapshot. | Missing optional regions do not block startup. |
| `FR-UI-DISCOVER_WORKSPACES` | Discover authorized workspace routes and commands from compatible contributions. | No hard-coded provider imports or registration order dependency. |
| `FR-UI-SWITCH_WORKSPACES` | Switch workspaces while preserving scoped state and preventing hidden workspaces from intercepting input. | Exactly one workspace owns the active interaction target. |
| `FR-UI-SHOW_CAPABILITY_STATE` | Distinguish loading, unavailable, incompatible, disabled, degraded, unauthorized, and ready capabilities. | Missing domain never appears as a blank or indefinitely loading screen. |
| `FR-UI-RESTORE_ROUTE` | Restore only a still-authorized, compatible route and otherwise select a deterministic fallback. | Removed routes cannot be resurrected by saved client state. |

## Capabilities

- **Provides:** `ui.compose-shell@1`
- **Required Capabilities:** None
- **Optional Capabilities:**
  - `workspace.manage-workspaces@1`
  - `workspace.build-diagnostics@1`
  - `plugins.declare-manifests@1`
  - `interfaces.serve-api-events@1`

## Configuration

| Setting | Type | Default | Description |
| --- | --- | --- | --- |
| `default_route` | string | `"/home"` | Default route path to fallback to when requested route is missing. |
| `show_footer` | boolean | `true` | Whether to display the optional shell footer. |
| `title` | string | `"HaruQuantAI"` | Title brand rendered in the shell header. |

## Interactive Usage Workflow

1. **Initialize UI Runtime:** Initialize `UiCompositionBridge` with active system capabilities and UI feature manifests.
2. **Mount Shell:** Mount `<Shell />` inside `<UiRuntimeProvider bridge={bridge}>`.
3. **Inspect Shell Structure:** The header renders brand title and `<WorkspaceSwitcher />`.
4. **Discover Workspaces:** Discovered authorized workspaces appear as tabs in the navigation bar.
5. **Switch Active Workspace:** Select a workspace tab (via click or keyboard). The workspace outlet updates to render the selected workspace and acquires main interaction focus.
6. **Observe Capability State:** The status bar renders badges for all registered capabilities, clearly reflecting `ready`, `loading`, `degraded`, `unavailable`, `disabled`, `unauthorized`, or `incompatible`.
7. **Restore / Fallback Route:** Navigation requests to authorized routes restore the workspace; requests to removed or unauthorized routes redirect deterministically to `default_route`.

## Failure Behavior

- If an optional capability is absent or fails, the shell remains operational and presents an explicit `unavailable` or `degraded` badge in the status bar.
- If a route is unauthorized or uninstalled, `RouteManager` rejects resurrection and redirects to the configured fallback route without crashing.
- If a workspace component throws an error, it is isolated from the shell navigation and header.

## Removal Behavior

Removing `FEAT-UI-COMPOSE_SHELL` removes the graphical shell and top-level navigation container. Non-UI clients (API, CLI, MCP) and background services continue uninterrupted.
