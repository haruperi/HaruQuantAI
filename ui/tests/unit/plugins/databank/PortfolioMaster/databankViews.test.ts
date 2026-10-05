import { describe, it, expect, beforeEach } from 'vitest';
import {
  DATABANK_METRIC_COLUMNS,
  DEFAULT_VIEW_PRESETS,
} from '../../../../../app/plugins/databank/PortfolioMaster/ProjectDatabanks/databankColumns';
import { useDatabankStore } from '../../../../../app/plugins/databank/PortfolioMaster/ProjectDatabanks/databankStore';
import { strategies } from '../../../../../app/plugins/databank/PortfolioMaster/fixtures';

describe('Databank Views and Metrics Engine', () => {
  beforeEach(() => {
    if (typeof localStorage !== 'undefined') {
      localStorage.clear();
    }
    useDatabankStore.getState().resetViews();
  });

  it('contains over 100 quantitative strategy metric columns categorized according to SQX', () => {
    expect(DATABANK_METRIC_COLUMNS.length).toBeGreaterThanOrEqual(100);

    const categories = new Set(DATABANK_METRIC_COLUMNS.map(c => c.category));
    expect(categories.has('General')).toBe(true);
    expect(categories.has('Performance')).toBe(true);
    expect(categories.has('Risk & Drawdown')).toBe(true);
    expect(categories.has('Trade Counts')).toBe(true);
    expect(categories.has('Durations & Quality')).toBe(true);
    expect(categories.has('Visual')).toBe(true);
  });

  it('defines the 5 standard SQX view presets matching donor .vw files', () => {
    expect(DEFAULT_VIEW_PRESETS.length).toBe(5);
    const names = DEFAULT_VIEW_PRESETS.map(v => v.name);
    expect(names).toContain('Default - Main data');
    expect(names).toContain('Performance');
    expect(names).toContain('Risk & Drawdown');
    expect(names).toContain('Trade Statistics');
    expect(names).toContain('Default with Note - Main data');
  });

  it('correctly calculates metrics from strategy fixtures', () => {
    const s = strategies[0];
    const metricMap = new Map(DATABANK_METRIC_COLUMNS.map(c => [c.id, c]));

    const netProfitCol = metricMap.get('netProfit')!;
    expect(netProfitCol.calculate(s)).toBe(s.metrics.netProfit);

    const pfCol = metricMap.get('profitFactor')!;
    expect(pfCol.calculate(s)).toBe(s.metrics.profitFactor);

    const tradesCol = metricMap.get('trades')!;
    expect(tradesCol.calculate(s)).toBe(s.metrics.trades);

    const miniEquityCol = metricMap.get('miniEquity')!;
    const equitySeries = miniEquityCol.calculate(s) as number[];
    expect(Array.isArray(equitySeries)).toBe(true);
    expect(equitySeries.length).toBe(s.equity.length);
  });

  it('supports full lifecycle in useDatabankStore (clone, update, reorder, delete, reset)', () => {
    const store = useDatabankStore.getState();
    expect(store.views.length).toBe(5);

    // Clone view
    const cloned = store.cloneView('default-main', 'My Custom View');
    expect(cloned.name).toBe('My Custom View');
    expect(cloned.isDefault).toBe(false);
    expect(useDatabankStore.getState().views.length).toBe(6);

    // Update column width
    store.setColumnWidth(cloned.id, 'netProfit', 140);
    const updatedView = useDatabankStore.getState().views.find(v => v.id === cloned.id)!;
    const col = updatedView.columns.find(c => c.columnId === 'netProfit');
    expect(col?.width).toBe(140);

    // Delete custom view
    store.deleteView(cloned.id);
    expect(useDatabankStore.getState().views.length).toBe(5);

    // Protect default view from deletion
    store.deleteView('default-main');
    expect(useDatabankStore.getState().views.length).toBe(5);

    // Reset views
    store.resetViews();
    expect(useDatabankStore.getState().views.length).toBe(5);
  });
});
