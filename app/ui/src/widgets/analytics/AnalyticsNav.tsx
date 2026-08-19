/**
 * Analytics 7-tab sub-navigation (FEAT-UI-32).
 *
 * Provides tab-based switching across all 18 Analytics-owned analytical sections:
 * 1. Overview (summary, ratios, quality flags)
 * 2. Returns & VAMI (monthly returns, returns series, VAMI)
 * 3. Drawdown & Risk (drawdown curves, underwater periods, streaks)
 * 4. Trade Analysis (trade ledger, distribution, duration, outliers, excursions)
 * 5. Grouped Performance (period tables, calendar heatmap)
 * 6. Benchmark & Costs (relative returns, alpha/beta, slippage, commission)
 * 7. Artifacts & Replay (reports, result refs, replay anchors)
 */

"use client";

import type { ReactNode } from "react";
import {
  Archive,
  Calendar,
  DollarSign,
  LayoutDashboard,
  ListOrdered,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

export type AnalyticsTab =
  | "overview"
  | "returns"
  | "drawdown"
  | "trades"
  | "grouped"
  | "benchmark"
  | "artifacts";

export interface AnalyticsTabDef {
  id: AnalyticsTab;
  label: string;
  description: string;
  icon: typeof LayoutDashboard;
}

export const ANALYTICS_TABS: ReadonlyArray<AnalyticsTabDef> = [
  {
    id: "overview",
    label: "Overview",
    description: "Key metrics, risk-adjusted ratios, and data quality indicators",
    icon: LayoutDashboard,
  },
  {
    id: "returns",
    label: "Returns & VAMI",
    description: "Equity curves, monthly performance matrix, and wealth growth index",
    icon: TrendingUp,
  },
  {
    id: "drawdown",
    label: "Drawdown & Risk",
    description: "Underwater drawdown curves, drawdown durations, and win/loss streaks",
    icon: TrendingDown,
  },
  {
    id: "trades",
    label: "Trade Analysis",
    description: "Canonical closed trade ledger, MAE/MFE excursions, duration, and outliers",
    icon: ListOrdered,
  },
  {
    id: "grouped",
    label: "Grouped Performance",
    description: "Multi-dimension period aggregations and trade calendar activity",
    icon: Calendar,
  },
  {
    id: "benchmark",
    label: "Benchmark & Costs",
    description: "Benchmark comparison, tracking error, commission, swap, and cost drag",
    icon: DollarSign,
  },
  {
    id: "artifacts",
    label: "Artifacts & Replay",
    description: "Attached reports, simulation result references, and journal replay anchors",
    icon: Archive,
  },
];

export interface AnalyticsNavProps {
  activeTab: AnalyticsTab;
  onTabChange: (tab: AnalyticsTab) => void;
  className?: string;
}

export function AnalyticsNav({
  activeTab,
  onTabChange,
  className = "",
}: AnalyticsNavProps): ReactNode {
  return (
    <nav
      className={`analytics-nav ${className}`}
      role="tablist"
      aria-label="Analytics Sections"
    >
      {ANALYTICS_TABS.map((tab) => {
        const Icon = tab.icon;
        const isSelected = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            role="tab"
            id={`analytics-tab-${tab.id}`}
            aria-selected={isSelected}
            aria-controls={`analytics-panel-${tab.id}`}
            tabIndex={isSelected ? 0 : -1}
            className={`analytics-nav__tab-btn ${isSelected ? "analytics-nav__tab-btn--active" : ""}`}
            onClick={() => onTabChange(tab.id)}
          >
            <Icon className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
            <span>{tab.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
