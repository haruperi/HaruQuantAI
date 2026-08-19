'use client';

/**
 * Widget-type to widget-component rendering switch (FEAT-UI-01/16).
 *
 * Shared by layout hosts so every surface that shows a widget renders the
 * exact same component for a given widget type. Extracted from the former
 * WorkspaceGrid widget switch.
 */
import React from 'react';

import { MarketsWidget } from '../../widgets/markets';
import { MarketTicksTableWidget } from '../../widgets/market-ticks';
import { WatchlistWidget } from '../../widgets/watchlists';
import { ChartWidget } from '../../widgets/chart';
import { OptionsGridWidget } from '../../widgets/instrument-panels';
import { PriceLadderWidget } from '../../widgets/price-ladder';
import { TradePlanWidget } from '../../widgets/planning';
import { ChallengesWidget, EducationWidget } from '../../widgets/training-ux';
import { PositionsWidget, TradeLogWidget } from '../workflow';
import { DashboardView } from '../workflow/dashboard';
import { DataWorkspace } from '../workflow/data';
import { StrategyWorkspace } from '../workflow/strategies';
import { ResearchDashboard } from '../../widgets/research';
import { OptimizationView } from '../workflow/optimization';
import { PortfolioView } from '../workflow/portfolio';
import { AgenticView } from '../workflow/agentic';
import { SimulationHome } from '../../widgets/simulator';
import { RiskView } from '../workflow/risk';
import { TradingWidget } from '../../widgets/trading';
import { SessionRegistryWidget } from '../../widgets/session-registry';
import { IndicatorWorkspace } from '../workflow/indicators';
import { NewsWidget } from '../../widgets/news';
import { MarketHoursWidget } from '../../widgets/market-hours';
import { AnalyticsWorkspace } from '../../widgets/analytics';
import type { Widget } from '../../widgets/workspaces';

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
      return <SimulationHome />;
    case 'risk':
      return <RiskView />;
    case 'trading':
      return <TradingWidget accountId={widget.accountId} symbol={widget.symbol} />;
    case 'sessions':
      return <SessionRegistryWidget />;
    case 'indicators':
      return <IndicatorWorkspace />;
    case 'news':
      return <NewsWidget />;
    case 'market-hours':
      return <MarketHoursWidget />;
    case 'analytics':
      return <AnalyticsWorkspace runId={widget.runId} />;
    default:
      return <MarketsWidget />;
  }
};
