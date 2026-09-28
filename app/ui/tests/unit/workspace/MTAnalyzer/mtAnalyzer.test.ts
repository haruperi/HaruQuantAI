import { describe, expect, it, beforeEach } from 'vitest';
import { useMTAnalyzerStore, computeMetrics, parseMetaTraderHtml } from '../../../../app/workspace/MTAnalyzer/mtAnalyzerStore';
import type { MTStatementTrade } from '../../../../app/workspace/MTAnalyzer/documents';

describe('MetaTrader Statement Analyzer Store (FEAT-UI-MT-ANALYZER)', () => {
  beforeEach(() => {
    const store = useMTAnalyzerStore.getState();
    store.loadPreset('scalper');
  });

  it('initializes with default scalper statement trades and calculated SQX metrics', () => {
    const state = useMTAnalyzerStore.getState();
    expect(state.trades.length).toBeGreaterThan(50);
    expect(state.statementFileName).toContain('Scalper');
    expect(state.selectedPreset).toBe('scalper');

    const m = state.metrics;
    expect(m.totalTrades).toBe(state.filteredTrades.length);
    expect(m.initialDeposit).toBe(10000);
    expect(m.profitFactor).toBeGreaterThan(0);
    expect(m.winRate).toBeGreaterThan(0);
    expect(m.sqn).toBeDefined();
    expect(m.sharpeRatio).toBeDefined();
    expect(m.maximalDrawdown).toBeGreaterThanOrEqual(0);
  });

  it('accurately computes performance metrics and SQN from closed trade list', () => {
    const mockTrades: MTStatementTrade[] = [
      {
        ticket: 1,
        openTime: '2025-01-02 09:00:00',
        type: 'buy',
        size: 1.0,
        item: 'EURUSD',
        openPrice: 1.0800,
        closeTime: '2025-01-02 11:00:00',
        closePrice: 1.0850,
        commission: -3.5,
        swap: 0,
        profit: 500,
        pips: 50,
      },
      {
        ticket: 2,
        openTime: '2025-01-03 10:00:00',
        type: 'sell',
        size: 1.0,
        item: 'EURUSD',
        openPrice: 1.0850,
        closeTime: '2025-01-03 12:00:00',
        closePrice: 1.0870,
        commission: -3.5,
        swap: 0,
        profit: -200,
        pips: -20,
      },
      {
        ticket: 3,
        openTime: '2025-01-04 14:00:00',
        type: 'buy',
        size: 1.0,
        item: 'EURUSD',
        openPrice: 1.0870,
        closeTime: '2025-01-04 16:00:00',
        closePrice: 1.0900,
        commission: -3.5,
        swap: 0,
        profit: 300,
        pips: 30,
      },
    ];

    const result = computeMetrics(mockTrades, 10000);
    expect(result.totalTrades).toBe(3);
    expect(result.grossProfit).toBe(800);
    expect(result.grossLoss).toBe(200);
    expect(result.totalNetProfit).toBe(600);
    expect(result.profitFactor).toBe(4.0);
    expect(result.profitTrades).toBe(2);
    expect(result.lossTrades).toBe(1);
    expect(result.winRate).toBe(66.7);
    expect(result.expectedPayoff).toBe(200);
    expect(result.sqn).toBeGreaterThan(0);
  });

  it('switches between presets (trend, breakout) and updates trade collections', () => {
    const store = useMTAnalyzerStore.getState();

    store.loadPreset('trend');
    let state = useMTAnalyzerStore.getState();
    expect(state.selectedPreset).toBe('trend');
    expect(state.statementFileName).toContain('Trend');
    expect(state.trades.some((t) => t.item === 'GBPUSD')).toBe(true);

    store.loadPreset('breakout');
    state = useMTAnalyzerStore.getState();
    expect(state.selectedPreset).toBe('breakout');
    expect(state.statementFileName).toContain('Breakout');
    expect(state.trades.some((t) => t.item === 'USATECH.idx')).toBe(true);
  });

  it('filters trades by symbol and magic number, updating filtered count and recalculating metrics', () => {
    const store = useMTAnalyzerStore.getState();
    const initialTrades = store.trades;

    // Filter by specific symbol if present
    const firstSymbol = initialTrades[0].item;
    store.setFilters({ symbol: firstSymbol });

    const state = useMTAnalyzerStore.getState();
    expect(state.filters.symbol).toBe(firstSymbol);
    expect(state.filteredTrades.every((t) => t.item === firstSymbol)).toBe(true);
    expect(state.metrics.totalTrades).toBe(state.filteredTrades.length);

    // Reset filter
    store.setFilters({ symbol: 'ALL' });
    expect(useMTAnalyzerStore.getState().filteredTrades.length).toBe(initialTrades.length);
  });

  it('parses standard MetaTrader HTML statement format', () => {
    const sampleHtml = `
      <html>
        <body>
          <table>
            <tr><td colspan="10">Closed Transactions:</td></tr>
            <tr>
              <td>100101</td>
              <td>2025.01.05 10:00:00</td>
              <td>buy</td>
              <td>0.50</td>
              <td>EURUSD</td>
              <td>1.08200</td>
              <td>1.07800</td>
              <td>1.08900</td>
              <td>2025.01.05 14:30:00</td>
              <td>1.08600</td>
              <td>-1.75</td>
              <td>0.00</td>
              <td>200.00</td>
            </tr>
          </table>
        </body>
      </html>
    `;

    const parsed = parseMetaTraderHtml(sampleHtml);
    expect(parsed.length).toBeGreaterThanOrEqual(1);
    const trade = parsed[0];
    expect(trade.ticket).toBe(100101);
    expect(trade.type).toBe('buy');
    expect(trade.size).toBe(0.5);
    expect(trade.profit).toBe(200);
  });

  it('handles configure modal state and tab navigation', () => {
    const store = useMTAnalyzerStore.getState();
    expect(store.isConfigureModalOpen).toBe(false);

    store.setIsConfigureModalOpen(true);
    expect(useMTAnalyzerStore.getState().isConfigureModalOpen).toBe(true);

    store.setActiveTab('tradeAnalysis');
    expect(useMTAnalyzerStore.getState().activeTab).toBe('tradeAnalysis');

    store.setActiveTab('equityChart');
    expect(useMTAnalyzerStore.getState().activeTab).toBe('equityChart');
  });
});
