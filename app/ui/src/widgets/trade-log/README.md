# Trade Log Widget (`FEAT-UI-08`)

> **Package:** `app/ui/src/widgets/trade-log/`
> **System role:** Historical transaction logs, execution fills review, trade notes, and CSV export.
> **Status:** `Completed` — D-UI feature model (§4.8)

---

## 1. Feature Identity & Manifest

`FEAT-UI-08` declares the `TRADE_LOG_MANIFEST`:
- **Widget Type:** `tradeLog`
- **Optional Capabilities:** `interfaces.operate-trading@1`
- **Default Dimensions:** 800 × 300 px (minimum 400 × 180 px)
- **Placement:** Bottom workspace panel
- **Accessibility:** `role="region"`, `aria-live="polite"`

## 2. Configuration (`config.ts`)

Strict Zod schema (`tradeLogConfigSchema`):
- `defaultProduct: string` (default: `"All Products"`)
- `persistedStateSchemaVersion: 1` (strict literal)

Unknown fields and invalid values fail closed at the `TradeLogFeature` boundary.
