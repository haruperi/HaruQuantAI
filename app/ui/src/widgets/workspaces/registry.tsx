"use client";

/**
 * Sole lazy widget registry for FEAT-UI-COMPOSE_WORKSPACE.
 *
 * Availability is intentionally separate from feature acceptance. Existing
 * pre-V3 manifests remain visible as legacy, unqualified provenance; ratified
 * later V3 owners remain planned and unqualified until their own Task closes.
 */

import React, { lazy, useEffect } from "react";

import type { WidgetManifest } from "../../types/widget-manifest";
import { INSTRUMENT_PANELS_MANIFEST } from "../instrument-panels/manifest";
import { MARKET_HOURS_MANIFEST } from "../market-hours/manifest";
import { MARKET_TICKS_MANIFEST } from "../market-ticks/manifest";
import { MARKETS_MANIFEST } from "../markets/manifest";
import { NEWS_MANIFEST } from "../news/manifest";
import { POSITIONS_MANIFEST } from "../positions/manifest";
import { PRICE_LADDER_MANIFEST } from "../price-ladder/manifest";
import { TRADE_LOG_MANIFEST } from "../trade-log/manifest";
import { TRADE_PLAN_MANIFEST } from "../trade-plan/manifest";
import { TRADING_MANIFEST } from "../trading/manifest";
import { WATCHLISTS_MANIFEST } from "../watchlists/manifest";

/** Minimal safe widget view passed to lazy render adapters. */
export interface RegistryWidget {
  readonly id: string;
  readonly type: string;
  readonly title: string;
  readonly symbol?: string;
  readonly accountId?: string;
  readonly runId?: string;
}

export interface RegisteredWidgetProps {
  readonly widget: RegistryWidget;
}

/** Navigation data owned by the workspace catalogue. */
export interface WidgetNavigation {
  readonly domain: string;
  readonly label: string;
  readonly title: string;
  readonly symbol?: string;
  readonly icon: string;
}

/** Explicitly non-acceptance provenance for an available component. */
export interface WidgetQualification {
  readonly kind: "legacy-manifest" | "legacy-feature-id" | "legacy-surface" | "planned-feature";
  readonly ownerId: string;
  readonly status: "UNQUALIFIED";
}

/** Truthful catalogue descriptor; no undeclared effects or capabilities are synthesized. */
export interface WorkspaceWidgetDescriptor {
  readonly widgetType: string;
  readonly title: string;
  readonly description: string;
  readonly availability: "AVAILABLE";
  readonly qualification: WidgetQualification;
  readonly declaredManifest?: WidgetManifest;
}

export interface WorkspaceWidgetRegistration {
  readonly manifest: WorkspaceWidgetDescriptor;
  readonly navigation: WidgetNavigation;
  readonly load: () => Promise<{ default: React.ComponentType<RegisteredWidgetProps> }>;
  readonly migrateConfig: (value: unknown) => unknown;
  readonly createScope: () => () => void;
}

interface RegistrationSeed extends WidgetNavigation {
  readonly provenance: Omit<WidgetQualification, "status">;
  readonly declaredManifest?: WidgetManifest;
  readonly load: WorkspaceWidgetRegistration["load"];
}

function registration(
  widgetType: string,
  seed: RegistrationSeed,
): WorkspaceWidgetRegistration {
  return {
    manifest: {
      widgetType,
      title: seed.title,
      description:
        seed.declaredManifest?.description ??
        `${seed.label} component surface; no owning manifest has been qualified.`,
      availability: "AVAILABLE",
      qualification: { ...seed.provenance, status: "UNQUALIFIED" },
      declaredManifest: seed.declaredManifest,
    },
    navigation: {
      domain: seed.domain,
      label: seed.label,
      title: seed.title,
      symbol: seed.symbol,
      icon: seed.icon,
    },
    load: seed.load,
    migrateConfig: (value) => value,
    createScope: () => {
      let disposed = false;
      return () => {
        if (disposed) return;
        disposed = true;
      };
    },
  };
}

const legacyManifest = (manifest: WidgetManifest): RegistrationSeed["provenance"] => ({
  kind: "legacy-manifest",
  ownerId: manifest.featureId,
});

const legacyFeature = (ownerId: string): RegistrationSeed["provenance"] => ({
  kind: "legacy-feature-id",
  ownerId,
});

const plannedFeature = (ownerId: string): RegistrationSeed["provenance"] => ({
  kind: "planned-feature",
  ownerId,
});

const seeds = {
  markets: {
    provenance: legacyManifest(MARKETS_MANIFEST), declaredManifest: MARKETS_MANIFEST,
    domain: "data", label: "Markets", title: "Markets", icon: "globe",
    load: async () => { const loaded = await import("../markets"); return { default: () => <loaded.MarketsFeature /> }; },
  },
  marketTicks: {
    provenance: legacyManifest(MARKET_TICKS_MANIFEST), declaredManifest: MARKET_TICKS_MANIFEST,
    domain: "data", label: "Market Ticks", title: "Market Ticks", icon: "activity",
    load: async () => { const loaded = await import("../market-ticks"); return { default: () => <loaded.MarketTicksFeature /> }; },
  },
  watchlist: {
    provenance: legacyManifest(WATCHLISTS_MANIFEST), declaredManifest: WATCHLISTS_MANIFEST,
    domain: "data", label: "Watchlists", title: "Watchlists", icon: "bookmark",
    load: async () => { const loaded = await import("../watchlists"); return { default: () => <loaded.WatchlistsFeature /> }; },
  },
  chart: {
    provenance: plannedFeature("FEAT-UI-MARKET_CHARTS"),
    domain: "indicators", label: "Chart", title: "EURUSD Chart", symbol: "EURUSD", icon: "line-chart",
    load: async () => { const loaded = await import("../chart"); return { default: ({ widget }: RegisteredWidgetProps) => <loaded.ChartWidget symbol={widget.symbol || "EURUSD"} widgetId={widget.id} /> }; },
  },
  priceLadder: {
    provenance: legacyManifest(PRICE_LADDER_MANIFEST), declaredManifest: PRICE_LADDER_MANIFEST,
    domain: "indicators", label: "Price Ladder", title: "ESU6 DOM", icon: "align-justify",
    load: async () => { const loaded = await import("../price-ladder"); return { default: ({ widget }: RegisteredWidgetProps) => <loaded.PriceLadderFeature config={{ defaultSymbol: widget.symbol || "EURUSD", accountId: widget.accountId }} /> }; },
  },
  optionsGrid: {
    provenance: legacyManifest(INSTRUMENT_PANELS_MANIFEST), declaredManifest: INSTRUMENT_PANELS_MANIFEST,
    domain: "indicators", label: "Options Grid", title: "Options Grid", icon: "layers",
    load: async () => { const loaded = await import("../instrument-panels"); return { default: ({ widget }: RegisteredWidgetProps) => <loaded.InstrumentPanelsFeature symbol={widget.symbol || "ESU5"} /> }; },
  },
  positions: {
    provenance: legacyManifest(POSITIONS_MANIFEST), declaredManifest: POSITIONS_MANIFEST,
    domain: "trading", label: "Positions & Orders", title: "Positions & Orders", icon: "list-ordered",
    load: async () => { const loaded = await import("../positions"); return { default: () => <loaded.PositionsFeature /> }; },
  },
  tradeLog: {
    provenance: legacyManifest(TRADE_LOG_MANIFEST), declaredManifest: TRADE_LOG_MANIFEST,
    domain: "trading", label: "Trade Log", title: "Trade Log", icon: "history",
    load: async () => { const loaded = await import("../trade-log"); return { default: () => <loaded.TradeLogFeature /> }; },
  },
  tradePlan: {
    provenance: legacyManifest(TRADE_PLAN_MANIFEST), declaredManifest: TRADE_PLAN_MANIFEST,
    domain: "resources", label: "Trade Plan", title: "My Trade Plan", icon: "file-spreadsheet",
    load: async () => { const loaded = await import("../trade-plan"); return { default: () => <loaded.TradePlanFeature /> }; },
  },
  education: {
    provenance: legacyFeature("FEAT-UI-11"),
    domain: "resources", label: "Education", title: "Education Resources", icon: "graduation-cap",
    load: async () => { const loaded = await import("../training-ux"); return { default: () => <loaded.EducationWidget /> }; },
  },
  challenges: {
    provenance: legacyFeature("FEAT-UI-12"),
    domain: "resources", label: "Challenges", title: "Challenges Dashboard", icon: "compass",
    load: async () => { const loaded = await import("../training-ux"); return { default: () => <loaded.ChallengesWidget /> }; },
  },
  dashboard: {
    provenance: plannedFeature("FEAT-UI-WORKSPACE_NAVIGATION"),
    domain: "resources", label: "Dashboard", title: "Dashboard", icon: "layout-dashboard",
    load: async () => { const loaded = await import("../../components/workflow/dashboard"); return { default: () => <loaded.DashboardView /> }; },
  },
  data: {
    provenance: plannedFeature("FEAT-UI-DATA_MANAGER"),
    domain: "data", label: "Data Explorer", title: "Data Explorer", icon: "database",
    load: async () => { const loaded = await import("../../components/workflow/data"); return { default: () => <loaded.DataWorkspace /> }; },
  },
  strategies: {
    provenance: plannedFeature("FEAT-UI-STRATEGY_STUDIO"),
    domain: "strategy", label: "Strategies", title: "Strategies", icon: "file-spreadsheet",
    load: async () => { const loaded = await import("../../components/workflow/strategies"); return { default: () => <loaded.StrategyWorkspace /> }; },
  },
  research: {
    provenance: plannedFeature("FEAT-UI-EXECUTE_ORDERS"),
    domain: "research", label: "Edge Lab", title: "Edge Lab", icon: "flask-conical",
    load: async () => { const loaded = await import("../research"); return { default: () => <loaded.ResearchDashboard /> }; },
  },
  optimization: {
    provenance: plannedFeature("FEAT-UI-PARAMETER_OPTIMIZER"),
    domain: "optimization", label: "Optimization", title: "Optimization", icon: "sliders",
    load: async () => { const loaded = await import("../../components/workflow/optimization"); return { default: () => <loaded.OptimizationView /> }; },
  },
  portfolio: {
    provenance: plannedFeature("FEAT-UI-PORTFOLIO_COMPOSER"),
    domain: "portfolio", label: "Portfolio", title: "Portfolio", icon: "pie-chart",
    load: async () => { const loaded = await import("../../components/workflow/portfolio"); return { default: () => <loaded.PortfolioView /> }; },
  },
  agentic: {
    provenance: plannedFeature("FEAT-UI-AGENTIC_RUN_INSPECTOR"),
    domain: "agentic", label: "Agentic Operator", title: "Agentic Operator", icon: "bot",
    load: async () => { const loaded = await import("../../components/workflow/agentic"); return { default: () => <loaded.AgenticView /> }; },
  },
  simulator: {
    provenance: plannedFeature("FEAT-UI-RUN_BACKTEST"),
    domain: "simulation", label: "Simulator", title: "Simulator", icon: "history",
    load: async () => { const loaded = await import("../simulator"); return { default: () => <loaded.SimulationHome /> }; },
  },
  risk: {
    provenance: { kind: "legacy-surface", ownerId: "components/workflow/risk" },
    domain: "risk", label: "Risk Governance", title: "Risk", icon: "alert-triangle",
    load: async () => { const loaded = await import("../../components/workflow/risk"); return { default: () => <loaded.RiskView /> }; },
  },
  trading: {
    provenance: legacyManifest(TRADING_MANIFEST), declaredManifest: TRADING_MANIFEST,
    domain: "trading", label: "Trading Cockpit", title: "Trading", icon: "trending-up",
    load: async () => { const loaded = await import("../trading"); return { default: ({ widget }: RegisteredWidgetProps) => <loaded.TradingFeature config={{ defaultSymbol: widget.symbol || "EURUSD", accountId: widget.accountId }} /> }; },
  },
  sessions: {
    provenance: legacyFeature("FEAT-UI-26"),
    domain: "trading", label: "Trading Sessions", title: "Trading Sessions", icon: "clock",
    load: async () => { const loaded = await import("../session-registry"); return { default: () => <loaded.SessionRegistryWidget /> }; },
  },
  indicators: {
    provenance: plannedFeature("FEAT-UI-INDICATOR_TESTER"),
    domain: "indicators", label: "Indicators Studio", title: "Indicators", icon: "trending-up",
    load: async () => { const loaded = await import("../../components/workflow/indicators"); return { default: () => <loaded.IndicatorWorkspace /> }; },
  },
  news: {
    provenance: legacyManifest(NEWS_MANIFEST), declaredManifest: NEWS_MANIFEST,
    domain: "data", label: "News", title: "News", icon: "newspaper",
    load: async () => { const loaded = await import("../news"); return { default: () => <loaded.NewsFeature /> }; },
  },
  "market-hours": {
    provenance: legacyManifest(MARKET_HOURS_MANIFEST), declaredManifest: MARKET_HOURS_MANIFEST,
    domain: "data", label: "Market Hours", title: "Market Hours", icon: "clock",
    load: async () => { const loaded = await import("../market-hours"); return { default: () => <loaded.MarketHoursFeature /> }; },
  },
  analytics: {
    provenance: plannedFeature("FEAT-UI-RESEARCH_WORKBENCH"),
    domain: "analytics", label: "Analytics", title: "Analytics", icon: "bar-chart-2",
    load: async () => { const loaded = await import("../analytics"); return { default: ({ widget }: RegisteredWidgetProps) => <loaded.AnalyticsWorkspace runId={widget.runId} /> }; },
  },
} as const satisfies Record<string, RegistrationSeed>;

export type WidgetType = keyof typeof seeds;

export const WIDGET_TYPES = Object.freeze(Object.keys(seeds)) as readonly WidgetType[];

const registrations = new Map<WidgetType, WorkspaceWidgetRegistration>(
  WIDGET_TYPES.map((widgetType) => [widgetType, registration(widgetType, seeds[widgetType])]),
);

const lazyComponents = new WeakMap<
  WorkspaceWidgetRegistration,
  React.LazyExoticComponent<React.ComponentType<RegisteredWidgetProps>>
>();

function lazyComponent(
  value: WorkspaceWidgetRegistration,
): React.LazyExoticComponent<React.ComponentType<RegisteredWidgetProps>> {
  const existing = lazyComponents.get(value);
  if (existing !== undefined) return existing;
  const created = lazy(value.load);
  lazyComponents.set(value, created);
  return created;
}

/** Return whether a value names an available registered widget contribution. */
export function isWidgetType(value: unknown): value is WidgetType {
  return typeof value === "string" && registrations.has(value as WidgetType);
}

/** Return the sole registered descriptor for a widget type. */
export function getWidgetRegistration(
  widgetType: string,
): WorkspaceWidgetRegistration | undefined {
  return registrations.get(widgetType as WidgetType);
}

/** Snapshot the current catalogue for navigation and template validation. */
export function listWidgetRegistrations(): readonly WorkspaceWidgetRegistration[] {
  return WIDGET_TYPES.flatMap((widgetType) => {
    const value = registrations.get(widgetType);
    return value === undefined ? [] : [value];
  });
}

/** Install one contribution and return its exact idempotent unregister disposer. */
export function registerWidget(
  widgetType: WidgetType,
  value: WorkspaceWidgetRegistration,
): () => void {
  const prior = registrations.get(widgetType);
  registrations.set(widgetType, value);
  let disposed = false;
  return () => {
    if (disposed) return;
    disposed = true;
    if (registrations.get(widgetType) !== value) return;
    if (prior === undefined) registrations.delete(widgetType);
    else registrations.set(widgetType, prior);
  };
}

/** Withdraw one contribution and return an idempotent exact restore disposer. */
export function withdrawWidget(widgetType: WidgetType): () => void {
  const prior = registrations.get(widgetType);
  registrations.delete(widgetType);
  let disposed = false;
  return () => {
    if (disposed) return;
    disposed = true;
    if (prior !== undefined && !registrations.has(widgetType)) {
      registrations.set(widgetType, prior);
    }
  };
}

/** Render a registered widget with scoped cleanup and explicit unavailable state. */
export function RegisteredWidgetContent({
  widget,
}: RegisteredWidgetProps): React.JSX.Element {
  const value = getWidgetRegistration(widget.type);
  useEffect(() => (value === undefined ? undefined : value.createScope()), [value]);

  if (value === undefined) {
    return (
      <section role="status" aria-label={`Missing widget: ${widget.title}`}>
        <h2>{widget.title}</h2>
        <p>
          Widget unavailable: the &quot;{widget.type}&quot; contribution is not
          registered in this build. Remove this panel or restore the owning
          widget feature.
        </p>
      </section>
    );
  }

  const Component = lazyComponent(value);
  return (
    <React.Suspense fallback={<p role="status">Loading {value.manifest.title}…</p>}>
      <Component widget={widget} />
    </React.Suspense>
  );
}
