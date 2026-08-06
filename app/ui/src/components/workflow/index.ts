/**
 * Workflow presentation components barrel (FEAT-API-11, Section 4.11).
 *
 * Auth-aware shell plus freshness-aware dashboard, read-only strategy
 * catalogue, backtest simulation, risk state, trading session, and Edge Lab
 * research, completed-run journal playback, and live what-if session views. Each consumes the typed clients and (for the shell) the auth
 * context built in Sections 4.9/4.10.
 */

export { AppShell } from "./shell";
export type { AppShellProps } from "./shell";

export { DashboardView } from "./dashboard";

export { StrategyWorkspace } from "./strategies";
export type { StrategyWorkspaceProps } from "./strategies";

export { IndicatorWorkspace } from "./indicators";
export type { IndicatorWorkspaceProps } from "./indicators";

export { SimulationView } from "./simulation";
export type { SimulationViewProps } from "./simulation";

export { RiskView } from "./risk";
export type { RiskViewProps } from "./risk";

export { TradingView } from "./trading";
export type { TradingViewProps } from "./trading";

export { ResearchWorkspace } from "./research";
export type { ResearchWorkspaceProps } from "./research";

export { PlaybackView } from "./playback";
export type { PlaybackViewProps } from "./playback";

export { WhatIfView } from "./whatIf";
export type { WhatIfViewProps } from "./whatIf";
