# HaruQuantAI UI Host Shell

> **Frontend Path:** `app/ui/app/host/`
> **Backend Counterpart:** `app/host/`
> **Role:** Universal Client Shell & Transport Hub
> **Status:** Implemented / Qualified
> **Last updated:** 2026-09-29

This README is the authoritative source of truth for the HaruQuantAI Frontend Host Shell. It owns universal browser navigation chrome, transport envelopes, session authentication handshakes, host boot screen visualization, and dynamic plugin discovery rendering.

[PROJECT.md](../../../../docs/PROJECT.md) owns system scope. [ARCHITECTURE.md](../../../../docs/ARCHITECTURE.md) owns structural rules and the Five Laws of Spatial Composability. [app/host/README.md](../../../host/README.md) owns the backend host contracts and lifecycle.

---

## 1. System Pair Overview

```text
Backend Host (app/host/)                 Frontend Host (app/ui/app/host/)
========================================================================================
- Five-phase boot lifecycle               - BootScreen (5-phase progress rendering)
- Process state management                - HostConnection (handshake & /app-loaded)
- Token verification & session repo       - In-memory bearer token management
- Dynamic catalog discovery (AST/JSON)    - Catalog cache & dynamic schema renderers
- JSON-RPC / REST envelope handling       - Universal transport (transport.ts)
- Host database persistence (SQLite)      - GlobalSettingsMenu & hostSettings.ts
- Resource custody & background jobs      - HeaderApplications & workspace navigation
```

The UI Host owns application chrome and universal communication infrastructure. It contains **zero** quantitative domain formulas, strategy definitions, or workspace workflow rules.

---

## 2. Boot Integration & Handshake (Schema Version 2)

The UI host couples to the backend host's boot contract **schema_version 2**:

1. **Boot Visualization:** `BootScreen.tsx` presents progress across the 5 canonical host phases: `runtime`, `services`, `packages`, `transport`, and `serving`.
2. **WebSocket Handshake:** `HostConnection.tsx` establishes authenticated WebSocket attachment (`/ws/updates`) and authenticates on the first frame within 5 seconds.
3. **Init-Data Ingestion:** Reads host configuration, discovered catalog snapshot, and presets via `GET /api/v1/init-data`.
4. **Client Acknowledgment:** Sends an idempotent POST to `/app-loaded` to record client arrival. Client arrival timing is decoupled from backend process boot timing.
5. **Fail-Closed Compatibility:** Rejects unsupported or missing `schema_version` snapshots with an explicit diagnostic modal.

---

## 3. Feature Registry & Traceability

In accordance with the Five-Level Structural Hierarchy, files in `app/ui/app/host/` represent traced UI features (`FEAT-UI-*`):

| Feature ID | Delivered Capability | Owner Files | Traced Operations | Verification Suite |
| :--- | :--- | :--- | :--- | :--- |
| `FEAT-UI-BOOT` | Boot sequence rendering, v2 handshake, client readiness | `BootScreen.tsx`<br>`HostConnection.tsx` | 5-phase visual progress, `/app-loaded` acknowledgment | `app/ui/tests/unit/host/bootSequence.test.tsx`<br>`app/ui/tests/unit/host/hostConnection.test.tsx` |
| `FEAT-UI-TRANSPORT` | Universal HTTP envelope, domain client factory, WebSockets | `transport.ts` | `createDomainClient()`, error mapping, request IDs | `app/ui/tests/unit/host/transport.test.ts` |
| `FEAT-UI-SESSIONS` | In-memory token acquisition, loopback auto-login, logout | `HostConnection.tsx`<br>`auth.ts` | Bearer token injection, session refresh, 401 handling | `app/ui/tests/unit/host/hostConnection.test.tsx` |
| `FEAT-UI-SETTINGS` | Global host settings projection, SSE stream subscription | `hostSettings.ts`<br>`GlobalSettingsMenu.tsx` | Scoped settings updates, credential redaction | `app/ui/tests/unit/host/hostSettings.test.ts` |
| `FEAT-UI-SHELL` | Top-level application chrome, dockview layout, tab router | `App.tsx`<br>`router.tsx`<br>`HeaderApplications.tsx` | Workspace switching, layout persistence | `app/ui/tests/unit/host/router.test.tsx` |

---

## 4. Spatial Composability & Transport Boundary Rules

1. **Envelope Ownership:** The host pair owns the request/response envelope `{api_version, request_id, status, data, error}`; domain pairs own their payload DTOs.
2. **Dynamic Slot Discovery:** Workspaces and plugins attach via explicit slots (e.g. `useAttachments('<slot_id>')`). The host shell imports zero concrete plugins statically.
3. **Isolation:** Workspace and plugin UI directories import universal primitives (`components/ui`), the host transport, and their own local files — never a sibling workspace's internal code.
4. **Honest View States:** The UI strictly presents backend truth; it never calculates simulated metrics or invents successful write states locally.

---

## 5. Verification and Definition of Done

| Verification Scope | Requirement | Command |
| :--- | :--- | :--- |
| **TypeScript Typing** | Zero type errors across frontend host and workspaces | `npm --prefix app/ui run typecheck` |
| **Unit Test Suite** | Boot, transport, sessions, and settings unit tests pass | `npm --prefix app/ui run test app/ui/tests/unit/host/` |
| **UI Architecture Check** | Slot attachments valid; zero direct static plugin imports | `node scripts/ui_architecture_check.cjs` |
| **Full Production Build** | Clean Vite build bundle generation | `npm --prefix app/ui run build` |
