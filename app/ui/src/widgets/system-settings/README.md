# System Settings Widget (`FEAT-UI-13`)

> **Package:** `app/ui/src/widgets/system-settings/`
> **System role:** Workstation modal for database-backed system settings, credentials, and runtime parameters.
> **Status:** `Completed` — D-UI feature model (§4.8)
> **Authoritative boundary:** Central `settings` and `settings_history` tables in `data/database/haruquantai.db` served through D-IFACE.

---

## 1. Feature Identity & Manifest

`FEAT-UI-13` declares the `SYSTEM_SETTINGS_MANIFEST`:
- **Widget Type:** `systemSettings`
- **Required Capabilities:** `interfaces.serve-api-events@1`
- **Optional Capabilities:** `none`
- **Default Dimensions:** 680 × 620 px (minimum 480 × 400 px)
- **Placement:** Floating modal host
- **Accessibility:** `role="dialog"`, `aria-live="polite"`, keyboard navigable

## 2. Configuration (`config.ts`)

Strict Zod schema (`systemSettingsConfigSchema`):
- `refreshOnOpen: boolean` (default: `true`)
- `persistedStateSchemaVersion: 1` (strict literal)

Unknown fields and invalid values fail closed at the `SystemSettingsFeature` boundary.

## 3. Architecture & Lifecycle

- `SystemSettingsFeature` manages config validation and error rendering.
- `SystemSettingsModal` provides focused presentation, category filters, and optimistic concurrency on save.
- All reads and writes target the central `settings` table in `haruquantai.db`.
