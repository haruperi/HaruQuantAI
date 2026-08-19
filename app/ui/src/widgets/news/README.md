# News Online Feed Widget

> **Feature ID:** `FEAT-UI-29`
> **Status:** `Completed`
> **Owning Package:** `app/ui`
> **Module Path:** `src/widgets/news/`

---

## 1. Overview

The News Online Feed Widget presents live, streaming financial and market news dynamically from Dukascopy's Online News Applet feed without requiring dedicated backend ingestion.

The applet runs inside an isolated, sandboxed `iframe` with custom dark CME-themed styling injected into the `srcDoc`. Dukascopy's native category tabs and language selector handle all feed interaction, eliminating redundant controls from the host toolbar.

---

## 2. Public API Surface

- `NewsWidget`: The primary React component rendering the widget container, title bar, live status badge, and embedded iframe.
- `NEWS_CATEGORIES`: Supported category constants (`finance`, `forex`, `stocks`, `company_news`, `commodities`).
- `NEWS_LANGUAGES`: 22 supported ISO language codes.
- `CATEGORY_LABELS`, `LANGUAGE_LABELS`: Human-readable display labels.
- `NewsWidgetProps`: Typed configuration properties (`className`, `defaultCategories`, `defaultLanguage`, `height`).

---

## 3. Requirements & Test Evidence

| Requirement ID | Description | Test Evidence |
| :--- | :--- | :--- |
| `FR-UI-253` | Render Dukascopy Online News feed in an isolated, sandboxed `iframe` with dark theme injection. | `NewsWidget.test.tsx` |
| `FR-UI-254` | Pass configured categories directly to the Dukascopy applet parameters. | `NewsWidget.test.tsx` |
| `FR-UI-255` | Support language configuration across 22 supported languages defaulting to English (`en`). | `NewsWidget.test.tsx` |
| `FR-UI-256` | Provide live status badge and loading overlay during iframe initialization. | `NewsWidget.test.tsx` |
| `FR-UI-257` | Register the `news` widget type in workspace contracts, allowing docking and layout persistence. | `WidgetContentHost.test.tsx`, `Sidebar.tsx` |
| `FR-UI-258` | Provide a standalone workstation page route (`/workstation/news`) with full-screen layout. | `pages.contract.test.ts` |
