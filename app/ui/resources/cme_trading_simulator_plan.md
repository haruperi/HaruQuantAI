# HaruQuantAI Trading Simulator UI - Full Implementation Plan

This plan outlines the complete frontend UI architecture, design system, component hierarchy, mock data structures, and implementation roadmap to rebuild the **HaruQuantAI Practice & Challenge Trading Simulator UI** exactly as specified in the reference guide.

---

## 1. Executive Summary & Design Overview

The goal is to build an accurate, pixel-perfect, highly responsive trading UI for **HaruQuantAI Practice & Challenge Trading Simulator**. The interface will operate as a modular, multi-workspace trading workstation equipped with real-time simulated market data, interactive charts, Depth of Market (DOM) price ladders, dual-side Options grids, order tickets, trade management, education portals, and challenge dashboards.

### Key Visual & Aesthetic Principles (CME Group Design System)
* **Color Palette**:
  * Primary Dark Navy / CME Deep Blue: `#0a192f` / `#0f2042` / `#162b53`
  * Accent Cyan / CME Brand Light Blue: `#00A3E0` / `#0072CE` / `#00c8ff`
  * Positive / Long / Buy: `#00b894` / `#26a69a` (Vibrant Emerald / Teal-Green)
  * Negative / Short / Sell: `#d63031` / `#ef5350` (Vibrant Crimson Red)
  * Soft Highlight Bids/Asks: Translucent Teal `#26a69a22` and Translucent Red `#ef535022`
  * Text & Typography: Modern sans-serif (`Inter` or `Outfit`), high contrast white `#ffffff` and muted gray `#a0aec0`
* **Layout Structure**:
  * Top Navigation Bar (Header with Account Status, 1-Click Toggle, Workspace Tabs)
  * Left Navigation Bar (Collapsible Sidebar with Widget Library, Challenges, Resources)
  * Modular Workspace Grid (Drag-and-drop dockable widget windows with min/max/close controls)

---

## 2. Technical Stack & Dependencies

* **Core Framework**: React 18 / 19 with Vite (Fast HMR, ESBuild)
* **Styling**: Vanilla CSS / CSS Modules / Tailored CSS Custom Variables (`index.css`) with rich glassmorphism & dark-mode aesthetics
* **State Management**: Zustand / React Context (Local state for quotes, positions, orders, active widgets, workspaces, practice/challenge mode)
* **Interactive Charting**: Lightweight Charts / Canvas API / SVG Custom Candlestick & Technical Indicators Renderer
* **Drag-and-Drop Grid**: Drag-and-Drop Docking Layout Engine / `react-grid-layout`
* **Icons**: `lucide-react` (matching CME icon set: line charts, ladders, options, target, settings, search, trophies, books)

---

## 3. Modular Architecture & Component Hierarchy

```
frontend/
├── index.html
├── package.json
├── vite.config.js
├── resources/
│   ├── documentation.pdf
│   ├── new-trading-sim-monitor_1500x1000.webp
│   └── cme_trading_simulator_plan.md
└── src/
    ├── main.jsx
    ├── index.css                   # Theme variables, global reset, dark workspace tokens
    ├── store/
    │   └── useTradingStore.js      # Mock quote feeds, order execution engine, account state
    ├── components/
    │   ├── common/
    │   │   ├── Button.jsx
    │   │   ├── Modal.jsx
    │   │   ├── ToggleSwitch.jsx
    │   │   └── TabGroup.jsx
    │   ├── layout/
    │   │   ├── Header.jsx          # Top account ticker, 1-Click toggle, Workspace tab bar
    │   │   ├── Sidebar.jsx         # Left menu (Hide Menu, Add Widgets, Challenges, Resources)
    │   │   └── WorkspaceGrid.jsx   # Grid container hosting draggable widgets
    │   ├── widgets/
    │   │   ├── MarketsWidget.jsx      # Asset categories (Equities, Energy, Metals, FX, etc.)
    │   │   ├── WatchlistWidget.jsx    # Custom watchlists & product picker
    │   │   ├── ChartWidget.jsx        # Interactive candlestick chart + indicators + quick buy/sell
    │   │   ├── PriceLadderWidget.jsx  # Depth of Market (DOM) vertical ladder with bid/ask depth
    │   │   ├── OptionsGridWidget.jsx   # Dual Calls/Puts chain with strike column
    │   │   ├── OrderTicketModal.jsx   # Futures & Options order submission dialog
    │   │   ├── PositionsWidget.jsx    # Open/Closed positions table with Flatten action
    │   │   ├── OrdersWidget.jsx       # Working/Filled/Cancelled orders table with Cancel/Amend
    │   │   ├── TradeLogWidget.jsx     # Historical execution audit log with notes drawer
    │   │   ├── TradePlanWidget.jsx    # Risk management parameters & trading goals questionnaire
    │   │   ├── EducationWidget.jsx    # CME Institute courses & video library
    │   │   └── ChallengesWidget.jsx   # Public & Private challenge registration & leaderboard
    └── mock/
        ├── productsData.js        # E-mini S&P (ES), Micro Nasdaq (MNQ), Gold (GC), Crude (CL), etc.
        ├── optionsData.js         # Option strike prices, calls & puts chains
        └── educationData.js       # CME courses and video tutorial metadata
```

---

## 4. Comprehensive Feature Specifications

### 4.1 Header & Top Bar
* **Account Financial Summary**:
  * `PRACTICE FUNDS`: $100,000.00 (with 'Reset Balance' functionality)
  * `NET P/L` / `PROFIT/LOSS`: Real-time computed profit/loss ($)
  * `MARGIN`: Dynamically calculated initial/maintenance margin
  * `AVAILABLE`: Net available purchasing power
  * `RANKING`: Leaderboard position indicator (active during Challenge mode, e.g. "2nd")
* **Workspace Tabs Navigation**:
  * Active tab indicator (e.g. `CME Group Works...`, `New Workspace-1`)
  * `+` button to spawn new custom workspaces (up to 10 workspaces supported)
  * Tab rename, duplicate, and close options
* **1-Click Trading Switch**:
  * Toggle switch with tooltip info: Enables instant market/ladder order placement without confirmation modals.
* **Account Mode Selector**:
  * Dropdown switcher between `Practice Mode` (Default) and `Challenge Mode` (Trophy badge, custom leaderboard metrics).

### 4.2 Sidebar Menu (Collapsible "HIDE MENU")
* **Add Widgets**:
  * Markets, Watchlists, Chart, Price Ladder, Options, Positions, Orders, Commentary, Calendar
* **Challenge**:
  * Discover, Dashboard
* **Resources**:
  * Education, Trade Plan, Trade Log, Help, Feedback, About, Legal

### 4.3 Featured Widgets

#### 1. Markets Widget
* Asset Class Tabs: `Equity Index`, `Energy`, `Metals`, `FX`, `Interest Rates`, `Agriculture`, `Cryptocurrencies`.
* Table Columns: Name, Contract Month (dropdown select: e.g., MNQU5, ESU5, MESU5, NQU5), Last Price, Change (Abs & %), Open, Prior Settle, High, Low, Volume, Actions.
* Row Actions: `TRADE` button (opens Order Ticket), Three-dots (`⋮`) menu offering `Chart`, `Price Ladder`, or `Options`.

#### 2. Watchlist Widget
* Category filters & product checklist drawer.
* "Create New", "Save A Copy", "Add To Workspace".
* Quick-action table with drag handles for reordering and instant `TRADE` launcher.

#### 3. Charting Tools Widget
* Header toolbar: Symbol selector, timeframe selector (`1m`, `5m`, `1h`, `1d`, `5d`, `1y`), chart type (Candles, Bars, Line), Technical Indicators menu (MA, EMA, MACD, RSI, Bollinger Bands, Stochastic, Fibonacci).
* Left toolbar: Drawing tools (Trendline, horizontal line, text annotation, zoom, magnet, measure, delete).
* Chart Canvas: High-performance real-time updating candles + volume bar pane.
* Overlay Quick Trade Buttons: Red `SELL [Price]` and Blue `BUY [Price]` overlaid directly on top of the chart header.

#### 4. Price Ladder / Depth of Market (DOM) Widget
* Top Controls: Time-in-Force (`DAY`, `GTC`), `FLATTEN`, `CANCEL ALL`, `BUY MKT`, Qty Stepper (`- 1 +`), `SELL MKT`.
* Real-time quote bar: `BID`, `ASK`, `LAST`, `VOLUME`, `CHANGE`.
* Vertical Depth Table:
  * Left: QTY (Working buy orders, cancel `X` button)
  * Center Left: BUY (Bid depth volume bars and order sizes)
  * Center: PRICE (Ascending/Descending price ticks)
  * Center Right: SELL (Ask depth volume bars and order sizes)
  * Right: QTY (Working sell orders, cancel `X` button)
* Bottom Controls: Cancel All (`X`), Re-Center (`Target icon` or Spacebar), Scroll arrows.

#### 5. Order Ticket Dialog (Futures & Options)
* Header: Product symbol, current Bid/Ask/Last quote banner.
* Tabs: `Futures` | `Options`
* Side Selector: `BUY` (Blue) vs `SELL` (Red)
* Order Types: `Market`, `Limit`, `Stop`, `Stop Limit`
* Parameters: Quantity (`- 1 +`), Time-in-Force (`DAY` / `GTC`), Limit Price, Stop Price.
* Bracket Order Setup: Take Profit / Stop Loss toggles (ticks / target price).
* Options Specific Fields: Expiration date dropdown, Put/Call toggle (`PUT` / `CALL`), Strike price selector (ATM ± 20 strikes).
* Submit Button: Prominent `BUY` / `SELL` execution trigger.

#### 6. Options Grid Widget
* Header: Underlying Futures Contract selector (e.g. `ESU5`), Last Price, Change, Prior Settle, High, Low, Volume.
* Dual Matrix Layout:
  * Left Side: CALLS (Low, High, Prior, Change, Last, Qty, Bid, Offer)
  * Center Column: STRIKE PRICE (Highlighting At-The-Money strike)
  * Right Side: PUTS (Bid, Offer, Qty, Last, Change, Prior, Low, High)
* Clickable Bid/Offer cells that instantly pop open pre-configured Order Tickets.

#### 7. Positions & Orders Widgets
* **Positions Window**: Tabs (`All`, `Open`, `Closed`), `FLATTEN ALL POSITIONS` button. Columns: Symbol, Contract, Month, Strike, C/P, Position (e.g., Short 1, Long 2), Buys, Sells, Average Px, Unrealized P/L, Realized P/L, Actions (`TRADE`, `FLATTEN`).
* **Orders Window**: Tabs (`All`, `Working`, `Filled`, `Cancelled`), `CANCEL ALL` button. Columns: Side (BUY/SELL), Symbol, Month, Qty, Leaves, Type (LMT, STP, MKT), Fill Px, Limit Px, Stop Px, Status, Actions (`AMEND`, `CANCEL`).

#### 8. Trade Log Widget
* Daily transaction history table with group headers by product, trade date/time, open/close status, buy/sell, fill price, P&L, and an interactive "Add Notes" pen tool.

#### 9. Trade Plan Widget
* Structured questionnaire form:
  * Section A: Risk Parameters (Dollars to risk per trade, % willing to risk per trade, % buying power to commit)
  * Section B: Trading Decision Inputs (Fundamental vs Technical)
  * Section C: Types of Market Trends (Momentum vs Contra Trend)
  * Section D: Risk Reward Ratio (1:1, 2:1, 3:1, 4:1, 5:1)
  * Goals list & Save button.

#### 10. Education Resources Widget
* Filter Pills: `New to Futures`, `Options`, `Strategies`, `Risk Management`, `Financials`, `Commodities`.
* Course Cards with lesson counts & external link icons.
* Video thumbnail library with play modal overlays.

#### 11. Challenges Widget & Dashboard
* Public Challenges: Scheduled open events list with "JOIN" button and details.
* Private Challenges: Code entry field ("Enter your code here"), display name input, and T&C checkbox.
* Leaderboard ranking view with challenge metrics.

---

## 5. Mock Data & Real-Time Simulation Engine

To make the UI feel alive and responsive, `useTradingStore.js` will maintain:
1. **Real-time Price Tickers**: Micro-animations and random-walk price fluctuation for active contracts (ES, NQ, GC, CL, ZC, 6E, etc.).
2. **Order Execution Simulator**: Placing Market/Limit/Stop orders updates the Orders list, populates Positions upon fill, computes live Unrealized P/L based on current tick prices, and updates account equity.
3. **Workspace Layout Persistence**: Saves current workspace state (added widgets, window positions, active tab) to `localStorage`.

---

## 6. Implementation Stages & Roadmap

* **Stage 1**: Foundation & Project Setup
  * Initialize Vite + React project structure in `frontend/`
  * Configure CSS design tokens (colors, typography, custom scrollbars, widget borders)
* **Stage 2**: Core Navigation & Layout Setup
  * Build `Header.jsx` with financial ticker bar, 1-Click toggle, and workspace tabs
  * Build `Sidebar.jsx` collapsible drawer with complete CME Group menu items
  * Build `WorkspaceGrid.jsx` window docking engine
* **Stage 3**: Primary Trading Widgets Implementation
  * Build `MarketsWidget.jsx` with category filtering and month dropdowns
  * Build `WatchlistWidget.jsx` with custom list builder
  * Build `ChartWidget.jsx` canvas/charting interface with indicators and quick buy/sell overlays
  * Build `PriceLadderWidget.jsx` DOM price ladder with depth bars & 1-click execution
* **Stage 4**: Advanced Widgets & Dialogs
  * Build `OrderTicketModal.jsx` (Futures & Options order ticket)
  * Build `OptionsGridWidget.jsx` dual CALLS/PUTS chain
  * Build `PositionsWidget.jsx` and `OrdersWidget.jsx`
* **Stage 5**: Supporting Features & Tools
  * Build `TradeLogWidget.jsx`, `TradePlanWidget.jsx`, `EducationWidget.jsx`, and `ChallengesWidget.jsx`
* **Stage 6**: Interactivity, Mock Engine & Polish
  * Connect simulated real-time price updates & mock order execution
  * Fine-tune CSS animations, glassmorphic dark theme, and visual fidelity against CME Group reference images.

---

## 7. Verification & Testing Plan

* **Visual Verification**: Compare rendered components side-by-side with reference pages in `resources/documentation.pdf`.
* **Interactive Testing**:
  * Verify 1-Click trading toggle state changes.
  * Verify adding/removing/moving widgets across workspaces.
  * Test placing Market, Limit, Stop orders from DOM, Chart, and Markets tab.
  * Test order fill simulation, position updates, P/L recalculation, and FLATTEN ALL actions.
  * Test switching between Practice Mode and Challenge Mode.
