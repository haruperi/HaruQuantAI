# HaruQuantAI V3 — Browser and UI Test Harness Specification

## 1. Overview & Objectives

The UI acceptance harness validates real rendered behavior in `app/ui/` using:
- **Unit & Component Testing:** Vitest + React Testing Library (`npm run test`)
- **End-to-End Integration Testing:** Playwright (`npm run e2e`)
- **Static Invariant Checks:** ESLint + TypeScript strict typechecking (`npm run typecheck`)

## 2. Test Classification Principles

1. **Real Provider vs Stub:**
   - Real-provider browser tests connect to a live local HaruQuantAI ASGI server instance running on an ephemeral loopback port (`127.0.0.1:<port>`).
   - Component-level contract tests use mock HTTP responses via MSW (Mock Service Worker) or Jest/Vitest spies.
   - The test report must explicitly record whether each spec executed against a live ASGI backend or a contract stub.
2. **Deterministic Layouts & Fixtures:**
   - E2E tests start with a pristine, temporary workspace folder containing pinned fixture files.
   - Tests must prove workspace restore, panel tear-off/docking, and clean unmount without dangling state or browser console errors.
3. **Accessibility & Diagnostics:**
   - Each phase checkpoint test verifies keyboard navigation, focus trap release, and axe-core accessibility compliance.
