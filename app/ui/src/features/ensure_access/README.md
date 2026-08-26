# FEAT-UI-ENSURE_ACCESS — Ensure Access

## 1. Purpose and Boundary

`FEAT-UI-ENSURE_ACCESS` is a cross-cutting accessibility feature providing the `ui.ensure-access@1` capability to the HaruQuantAI D-UI workstation. It requires `ui.compose-shell@1` for route and workspace outlet focus coordination.

Per `app/ui/README.md`, `FEAT-UI-ENSURE_ACCESS` contributes **no standalone widget**. Instead, it owns the root accessibility and focus presentation provider (`FocusManagerProvider`), coordinates deterministic workspace outlet focus transitions across route/workspace updates, and enforces non-color state distinction across UI surfaces.

## 2. Capability Contracts and Dependencies

- **Provided capability:** `ui.ensure-access@1`
- **Required capabilities:** `ui.compose-shell@1`
- **Optional capabilities:** None
- **Configuration:** Strict no-key configuration (`config.ts`), rejecting unknown properties.

## 3. Requirement Status (Partial — 2 of 6)

This feature implements the Stage 1.7 completable partial slice:

| Status | Requirement ID | Responsibility | Evidence |
|---|---|---|---|
| Implemented | `FR-UI-MANAGE_FOCUS` | Deterministic focus save/restore, rejection of detached/hidden/inert/disabled targets with fallback, and route/workspace outlet focus transfer. | `app/ui/src/accessibility/__tests__/focus_manager.test.tsx`, `app/ui/src/features/ensure_access/__tests__/ensure_access.test.tsx` |
| Implemented | `FR-UI-DISTINGUISH_STATE` | Non-color and motion-independent state distinction across shell readiness, activity log, product news, settings, and workspace templates. | `app/ui/src/features/compose_shell/__tests__/compose_shell.test.tsx`, `app/ui/src/widgets/activity_log/__tests__/activity_log.test.tsx`, `app/ui/src/widgets/product_news/__tests__/product_news.test.tsx`, `app/ui/src/widgets/settings/__tests__/settings.test.tsx`, `app/ui/src/widgets/workspace_templates/__tests__/workspace_templates.test.tsx` |
| Missing (Mock build) | `FR-UI-PROVIDE_DATA_ALTERNATIVES` | Tabular data alternatives for charts and graphical analytics (completes at Stage 10 Simulator de-mock gate — 10.15). | Deferred |
| Missing (Mock build) | `FR-UI-PRESERVE_USABILITY` | Viewport reflow, target sizing, contrast, and locale expansion (completes at Stage 3 Plugins de-mock gate — 3.11). | Deferred |
| Missing (Mock build) | `FR-UI-OPERATE_BY_KEYBOARD` | Full keyboard journey coverage across trading and order controls (completes at Stage 9 Trading de-mock gate — 9.10). | Deferred |
| Missing (Mock build) | `FR-UI-LABEL_CONTROLS` | Screen-reader control labels across operational trading surfaces (completes at Stage 9 Trading de-mock gate — 9.10). | Deferred |

## 4. Interactive Usage Workflow

1. Register `FEAT-UI-ENSURE_ACCESS` with `UiCompositionBridge` and wrap the workstation root with `ensureAccess.renderProvider(...)`.
2. When the user navigates between routes or switches workspaces, the route focus coordinator automatically focuses the active workspace panel outlet (`workspace-panel-<workspaceId>`), or `#workspace-panel-empty` if no route is active.
3. When dialogs, modals, or transient panels open, call `saveFocus(key)`. When dismissed, call `restoreFocus(key, fallbackElementId)`. If the target element was removed, hidden, made inert, or disabled, focus lands on the deterministic fallback.
4. Assistive announcements are dispatched via `announce(message, "polite" | "assertive")` to visually hidden live regions (`#a11y-live-polite`, `#a11y-live-assertive`).
5. Status indicators (readiness, notifications, applied templates, tab selections) present visible text, symbols, and ARIA attributes in addition to color and motion.

## 5. Failure and Removal Behavior

- **Invalid target failure:** When a saved focus target is detached from the DOM, hidden (`hidden` or `aria-hidden="true"`), inert, or disabled, `restoreFocus` detects the invalidity and focuses the designated fallback element ID or returns `false`.
- **Feature unregistration / removal:** Removing `FEAT-UI-ENSURE_ACCESS` from `UiCompositionBridge` marks `ui.ensure-access@1` unavailable in the shell capability state. The shell and remaining features continue functioning normally.
