# Positions & Orders Widget (`FEAT-UI-09`)

> **Package:** `app/ui/src/widgets/positions/`
> **System role:** Open positions monitoring, order lifecycle management, working orders filter, and flatten-all execution.
> **Status:** `Completed` — D-UI feature model (§4.8)

---

## 1. Feature Identity & Manifest

`FEAT-UI-09` declares the `POSITIONS_MANIFEST`:
- **Widget Type:** `positions`
- **Required Capabilities:** `interfaces.operate-trading@1`
- **Default Dimensions:** 800 × 260 px (minimum 400 × 180 px)
- **Placement:** Bottom workspace panel
- **Commands:** `trading.close-position`, `trading.cancel-order`
- **Subscriptions:** `trading.session-events`
- **Accessibility:** `role="region"`, `aria-live="polite"`

## 2. Configuration (`config.ts`)

Strict Zod schema (`positionsConfigSchema`):
- `defaultTab: "positions" | "orders"` (default: `"positions"`)
- `persistedStateSchemaVersion: 1` (strict literal)

Unknown fields and invalid values fail closed at the `PositionsFeature` boundary.
