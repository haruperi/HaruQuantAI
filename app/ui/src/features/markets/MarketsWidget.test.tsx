/** Markets widget column-population tests for FR-UI-058 and FR-UI-059. */

import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { MarketsWidget } from './MarketsWidget';

const { listMock, quotesMock } = vi.hoisted(() => ({
  listMock: vi.fn(),
  quotesMock: vi.fn(),
}));

vi.mock('../../store/useTradingStore', () => ({
  useTradingStore: () => ({
    openOrderTicket: vi.fn(),
    submitOrder: vi.fn(),
    oneClickTrading: false,
    addWidgetToWorkspace: vi.fn(),
  }),
}));

vi.mock('@/clients', () => ({
  apiClients: {
    watchlists: { list: listMock },
    data: { quotes: quotesMock },
  },
  unwrapData: (response: { data: unknown }) => response.data,
}));

const symbols = ['EURUSD', 'EURGBP', 'EURJPY', 'EURCHF', 'EURAUD'];

function marketRow(symbol: string, index: number): Record<string, unknown> {
  return {
    symbol,
    name: symbol,
    asset_class: 'Forex',
    source_id: 'mt5',
    digits: symbol.endsWith('JPY') ? 3 : 5,
    last: 1.105 + index * 0.001,
    bid: 1.105 + index * 0.001,
    ask: 1.1052 + index * 0.001,
    spread: 0.0002,
    volume: 1000 - index,
    open: 1.1,
    high: 1.108,
    low: 1.105,
    close: 1.107,
    change: 0.005,
    change_percent: 0.45,
    change_pips: 50,
    volatility: 12.5,
    adr: 50,
    range_percent_of_adr: 60,
  };
}

describe('MarketsWidget', () => {
  beforeEach(() => {
    listMock.mockResolvedValue({
      data: [
        {
          watchlist_id: 'wl-1',
          account_id: 'acct-1',
          name: 'default',
          is_default: true,
          sort_order: 0,
          items: symbols.map((symbol, sortOrder) => ({
            source_id: 'mt5',
            symbol,
            sort_order: sortOrder,
          })),
          created_at: '2026-08-12T00:00:00Z',
          updated_at: '2026-08-12T00:00:00Z',
        },
      ],
    });
    quotesMock.mockImplementation((requested: string[]) => ({
      data: {
        source_id: 'mt5',
        rows: requested.map((symbol) => marketRow(symbol, symbols.indexOf(symbol))),
        limit: requested.length,
        next_cursor: null,
        revision: '1.0.0',
        generated_at: '2026-08-12T00:00:00Z',
        request_id: 'req-1',
      },
    }));
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it('loads a large watchlist in sequential bounded batches', async () => {
    render(<MarketsWidget />);

    await waitFor(() => expect(quotesMock).toHaveBeenCalledTimes(2));

    expect(quotesMock.mock.calls[0][0]).toEqual(symbols.slice(0, 4));
    expect(quotesMock.mock.calls[1][0]).toEqual(symbols.slice(4));
    expect(quotesMock.mock.calls[0][1]).toEqual({ includeTechnicals: true });
  });

  it('renders the usage-contract values with their declared units', async () => {
    render(<MarketsWidget />);

    await screen.findByText('EURUSD');

    expect(screen.getAllByText('+50.0 (+0.45%)').length).toBeGreaterThan(0);
    expect(screen.getAllByText('12.50%').length).toBeGreaterThan(0);
    expect(screen.getAllByText('50.0 pips').length).toBeGreaterThan(0);
    expect(screen.getAllByText('60%').length).toBeGreaterThan(0);
    expect(screen.getAllByText('1.10500').length).toBeGreaterThan(0);
    expect(screen.getAllByText('1.10000').length).toBeGreaterThan(0);
    expect(screen.getAllByText('1.10800').length).toBeGreaterThan(0);
  });

  it('renders em dashes instead of inventing unavailable evidence', async () => {
    quotesMock.mockImplementation((requested: string[]) => ({
      data: {
        source_id: 'mt5',
        rows: requested.map((symbol) => ({
          ...marketRow(symbol, symbols.indexOf(symbol)),
          change: null,
          change_percent: null,
          change_pips: null,
          volatility: null,
          adr: null,
          range_percent_of_adr: null,
          open: null,
          high: null,
          low: null,
        })),
        limit: requested.length,
        next_cursor: null,
        revision: '1.0.0',
        generated_at: '2026-08-12T00:00:00Z',
        request_id: 'req-1',
      },
    }));

    render(<MarketsWidget />);
    await screen.findByText('EURUSD');

    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
  });
});
