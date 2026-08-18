'use client';

/**
 * Widget-type to widget-component rendering switch (FEAT-UI-01/16).
 *
 * Shared by layout hosts so every surface that shows a widget renders the
 * exact same component for a given widget type. Extracted from the former
 * WorkspaceGrid widget switch.
 */
import React from 'react';

import { MarketsWidget } from '../../features/markets';
import { MarketTicksTableWidget } from '../../features/market-ticks';
import { WatchlistWidget } from '../../features/watchlists';
import { ChartWidget } from '../../features/chart';
import { OptionsGridWidget } from '../../features/instrument-panels';
import { PriceLadderWidget } from '../../features/price-ladder';
import { TradePlanWidget } from '../../features/planning';
import { ChallengesWidget, EducationWidget } from '../../features/training-ux';
import { PositionsWidget, TradeLogWidget } from '../workflow';
import { DashboardView } from '../workflow/dashboard';
import { DataWorkspace } from '../workflow/data';
import { StrategyWorkspace } from '../workflow/strategies';
import { ResearchDashboard } from '../../features/research';
import { OptimizationView } from '../workflow/optimization';
import { PortfolioView } from '../workflow/portfolio';
import { AgenticView } from '../workflow/agentic';
import { SimulatorWidget } from '../../features/simulator';
import { RiskView } from '../workflow/risk';
import { TradingWidget } from '../../features/trading';
import { SessionRegistryWidget } from '../../features/session-registry';
import { IndicatorWorkspace } from '../workflow/indicators';
import type { Widget } from '../../features/workspaces';

export const WidgetContentHost: React.FC<{ widget: Widget }> = ({ widget }) => {
  switch (widget.type) {
    case 'markets':
      return <MarketsWidget />;
    case 'marketTicks':
      return <MarketTicksTableWidget />;
    case 'watchlist':
      return <WatchlistWidget />;
    case 'chart':
      return <ChartWidget symbol={widget.symbol || 'EURUSD'} widgetId={widget.id} />;
    case 'priceLadder':
      return <PriceLadderWidget symbol={widget.symbol} accountId={widget.accountId} />;
    case 'optionsGrid':
      return <OptionsGridWidget symbol={widget.symbol || 'ESU5'} />;
    case 'positions':
      return <PositionsWidget />;
    case 'tradeLog':
      return <TradeLogWidget />;
    case 'tradePlan':
      return <TradePlanWidget />;
    case 'education':
      return <EducationWidget />;
    case 'challenges':
      return <ChallengesWidget />;
    case 'dashboard':
      return <DashboardView />;
    case 'data':
      return <DataWorkspace />;
    case 'strategies':
      return <StrategyWorkspace />;
    case 'research':
      return <ResearchDashboard />;
    case 'optimization':
      return <OptimizationView />;
    case 'portfolio':
      return <PortfolioView />;
    case 'agentic':
      return <AgenticView />;
    case 'simulator':
      return <SimulatorWidget />;
    case 'risk':
      return <RiskView />;
    case 'trading':
      return <TradingWidget accountId={widget.accountId} symbol={widget.symbol} />;
    case 'sessions':
      return <SessionRegistryWidget />;
    case 'indicators':
      return <IndicatorWorkspace />;
    default:
      return <MarketsWidget />;
  }
};
