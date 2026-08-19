# FEAT-UI-30 FX Market Hours Widget

## 1. Purpose and Boundary

The **FX Market Hours Widget** (`FEAT-UI-30`) presents real-time session clocks and market data for the Asian, European, and North American FX trading sessions, alongside hourly spreads, volatility, and volume indicators dynamically from Dukascopy's FX Market Hours Applet within an isolated, sandboxed iframe container without requiring backend ingestion.

## 2. Package Structure

```text
app/ui/src/widgets/market-hours/
├── contracts.ts              # Widget props, config types, default CME themes, popular FX instruments
├── market-hours.module.css   # Dark theme CME styling for toolbar, iframe embed, and loader
├── MarketHoursWidget.tsx     # Focused React component embedding sandboxed Dukascopy Applet
├── MarketHoursWidget.test.tsx# Vitest unit and component tests
├── README.md                 # Canonical feature specification
└── index.ts                  # Sole public barrel export
```

## 3. Public API Surface

| Export | Kind | Description |
| :--- | :--- | :--- |
| `MarketHoursWidget` | Component | Primary widget rendering isolated trading clock iframe and host header |
| `DEFAULT_MARKET_HOURS_CONFIG` | Constant | Default configuration object for dark theme and interactive tools |
| `POPULAR_FX_INSTRUMENTS` | Constant | Array of primary FX currency pairs |
| `MarketHoursWidgetProps` | Interface | Component props interface |
| `MarketHoursWidgetConfig` | Interface | Dukascopy applet parameter schema |

## 4. Requirements & Evidence Matrix

| Status | Requirement ID | Responsibility | Component / Function / Type | Side Effects | Failure presentation | Usage / Test Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Completed | `FR-UI-259` | Render Dukascopy FX Market Hours feed in an isolated, sandboxed `iframe` with dark theme parameter injection and CSS reset, avoiding SPA virtual DOM disruption. | `MarketHoursWidget` | Iframe script execution | Explicit loading spinner and fallback message | `MarketHoursWidget.test.tsx` |
| Completed | `FR-UI-260` | Support configurable instrument default (`EUR/USD`, etc.) and indicator display modes (`0` for spreads/volatility/volume). | `MarketHoursWidget` | Iframe configuration | Default instrument fallback | `MarketHoursWidget.test.tsx` |
| Completed | `FR-UI-261` | Provide customizable timezone offset configuration defaulting to UTC/GMT (`0`). | `MarketHoursWidget` | Iframe configuration | Fallback to `0` UTC | `MarketHoursWidget.test.tsx` |
| Completed | `FR-UI-262` | Provide live status badge and loading overlay indicating external online data connectivity. | `MarketHoursWidget` | Iframe reload | Visual loading spinner during initialization | `MarketHoursWidget.test.tsx` |
| Completed | `FR-UI-263` | Register the `market-hours` widget type in workspace contracts, allowing docking, splitting, and layout persistence. | Workspace contracts, host | Layout persistence | Registered-type validation | `MarketHoursWidget.test.tsx` |
| Completed | `FR-UI-264` | Provide a standalone workstation page route (`/workstation/market-hours`) with full-screen layout. | `/workstation/market-hours` | Client routing | Protected layout | `MarketHoursWidget.test.tsx` |
