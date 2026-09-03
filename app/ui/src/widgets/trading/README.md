# Trading & Order Ticket Widget (`FEAT-UI-06`)

> **Package:** `app/ui/src/widgets/trading/`
> **System role:** Governed order entry, ticket preflight, execution session routing, and interactive price ladder execution.
> **Status:** `Completed` — D-UI feature model (§4.8)

---

## 1. Feature Identity & Manifest

`FEAT-UI-06` declares the `TRADING_MANIFEST`:
- **Widget Type:** `trading`
- **Required Capabilities:** `interfaces.operate-trading@1`
- **Optional Capabilities:** `data.stream-market-events@1`
- **Default Dimensions:** 720 × 600 px (minimum 360 × 320 px)
- **Placement:** Main workspace panel
- **Accessibility:** `role="region"`, `aria-live="polite"`

## 2. Configuration (`config.ts`)

Strict Zod schema (`tradingConfigSchema`):
- `defaultSymbol: string` (default: `"EURUSD"`)
- `ticketHostOnly: boolean` (default: `false`)
- `accountId?: string`
- `persistedStateSchemaVersion: 1` (strict literal)

Unknown fields and invalid values fail closed at the `TradingFeature` boundary.
