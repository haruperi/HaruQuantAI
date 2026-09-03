# Trade Plan Widget (`FEAT-UI-10`)

> **Package:** `app/ui/src/widgets/trade-plan/`
> **System role:** Pre-trade operational planning, risk boundaries, and execution rules.
> **Status:** `Completed` — D-UI feature model (§4.8)

---

## 1. Feature Identity & Manifest

`FEAT-UI-10` declares the `TRADE_PLAN_MANIFEST`:
- **Widget Type:** `tradePlan`
- **Optional Capabilities:** `trading.manage-trade-plans@1`
- **Default Dimensions:** 640 × 500 px (minimum 400 × 320 px)
- **Placement:** Main workspace panel
- **Accessibility:** `role="region"`, `aria-live="polite"`

## 2. Configuration (`config.ts`)

Strict Zod schema (`tradePlanConfigSchema`):
- `defaultRiskRewardRatio: string` (default: `"3:1"`)
- `persistedStateSchemaVersion: 1` (strict literal)

Unknown fields and invalid values fail closed at the `TradePlanFeature` boundary.
