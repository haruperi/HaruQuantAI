# Price Ladder (DOM) Widget (`FEAT-UI-05`)

> **Package:** `app/ui/src/widgets/price-ladder/`
> **System role:** Interactive depth-of-market ladder, price-level orders, cancels, working order tags, and position tracking.
> **Status:** `Completed` — D-UI feature model (§4.8)

---

## 1. Feature Identity & Manifest

`FEAT-UI-05` declares the `PRICE_LADDER_MANIFEST`:
- **Widget Type:** `priceLadder`
- **Required Capabilities:** `interfaces.operate-trading@1`
- **Optional Capabilities:** `data.stream-depth-events@1`
- **Default Dimensions:** 340 × 600 px (minimum 260 × 400 px)
- **Placement:** Right workspace panel
- **Commands:** `trading.submit-order`, `trading.cancel-order`
- **Subscriptions:** `data.depth-events`
- **Accessibility:** `role="region"`, `aria-live="polite"`

## 2. Configuration (`config.ts`)

Strict Zod schema (`priceLadderConfigSchema`):
- `defaultSymbol: string` (default: `"EURUSD"`)
- `variant: "standalone" | "trading"` (default: `"standalone"`)
- `accountId?: string`
- `persistedStateSchemaVersion: 1` (strict literal)

Unknown fields and invalid values fail closed at the `PriceLadderFeature` boundary.
