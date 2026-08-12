/** Focused unit evidence for Markets (FEAT-UI-02), FR-UI-030 through FR-UI-037. */

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { MarketsWidget } from './MarketsWidget';

const { marketsMock, listMock, openOrderTicketMock, submitOrderMock, addWidgetToWorkspaceMock } = vi.hoisted(() => ({
  marketsMock: vi.fn(),
  listMock: vi.fn(),
  openOrderTicketMock: vi.fn(),
  submitOrderMock: vi.fn(),
  addWidgetToWorkspaceMock: vi.fn(),
}));

vi.mock('../../store/useTradingStore', () => ({
  useTradingStore: () => ({
    openOrderTicket: openOrderTicketMock,
    submitOrder: submitOrderMock,
  }),
}));

let orderConfirmationRequired = true;
vi.mock('../workspaces', () => ({
  useWorkspaceStore: () => ({
    get orderConfirmationRequired() {
      return orderConfirmationRequired;
    },
    addWidgetToWorkspace: addWidgetToWorkspaceMock,
  }),
}));

vi.mock('@/clients', () => ({
  apiClients: {
    data: { markets: marketsMock },
    watchlists: { list: listMock },
  },
  unwrapData: (response: { data: unknown }) => response.data,
}));

function watchlist(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    watchlist_id: 'wl-1',
    account_id: 'acct-1',
    name: 'My List',
    is_default: false,
    sort_order: 0,
    items: [],
    created_at: '2026-08-12T00:00:00Z',
    updated_at: '2026-08-12T00:00:00Z',
    ...overrides,
  };
}

function marketRow(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    symbol: 'EURUSD',
    name: 'EURUSD',
    asset_class: 'Forex',
    source_id: 'mt5',
    digits: 5,
    last: 1.105,
    bid: 1.1049,
    ask: 1.1051,
    spread: 0.0002,
    volume: 1000,
    open: 1.1,
    high: 1.108,
    low: 1.105,
    close: 1.107,
    change: 0.005,
    change_percent: 0.45,
    ...overrides,
  };
}

function directoryPage(rows: Record<string, unknown>[], nextCursor: string | null): { data: unknown } {
  return {
    data: {
      source_id: 'mt5',
      rows,
      limit: rows.length,
      next_cursor: nextCursor,
      revision: '1.0.0',
      generated_at: '2026-08-12T00:00:00Z',
      request_id: 'req-1',
    },
  };
}

describe('MarketsWidget', () => {
  beforeEach(() => {
    orderConfirmationRequired = true;
    listMock.mockResolvedValue({ data: [] });
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it('reads the market directory, not a watchlist, with no client-elected source_id (FR-UI-033)', async () => {
    marketsMock.mockResolvedValue(directoryPage([marketRow()], null));

    render(<MarketsWidget />);
    await screen.findByText('EURUSD');

    expect(marketsMock).toHaveBeenCalledWith({ limit: 50, cursor: undefined });
    const [params] = marketsMock.mock.calls[0];
    expect(params).not.toHaveProperty('source_id');
  });

  it('renders pages progressively and caps at 4 pages even with an endless cursor (FR-UI-031)', async () => {
    marketsMock.mockImplementation((params: { cursor?: string }) =>
      Promise.resolve(
        directoryPage(
          [marketRow({ symbol: `SYM${params.cursor ?? '0'}`, name: `SYM${params.cursor ?? '0'}` })],
          `next-${(Number(params.cursor?.replace('next-', '') ?? '0') + 1)}`
        )
      )
    );

    render(<MarketsWidget />);
    await waitFor(() => expect(marketsMock).toHaveBeenCalledTimes(4));

    // Give the (already-resolved) 4th page a tick to flush into state, then
    // confirm a 5th page was never requested despite next_cursor never being null.
    await new Promise((resolve) => setTimeout(resolve, 10));
    expect(marketsMock).toHaveBeenCalledTimes(4);
    expect(screen.getAllByRole('row').length).toBeGreaterThan(1); // header + >=1 data row
  });

  it('surfaces a load failure explicitly rather than an empty table (FR-UI-032)', async () => {
    marketsMock.mockRejectedValue(new Error('network'));

    render(<MarketsWidget />);
    await screen.findByRole('alert');
    expect(screen.getByRole('alert').textContent).toMatch(/unable to load/i);
  });

  it('offers the fixed asset-class pills and filters the table (FR-UI-034)', async () => {
    marketsMock.mockResolvedValue(
      directoryPage(
        [
          marketRow({ symbol: 'EURUSD', name: 'EURUSD', asset_class: 'Forex' }),
          marketRow({ symbol: 'XAUUSD', name: 'XAUUSD', asset_class: 'Commodities' }),
        ],
        null
      )
    );

    render(<MarketsWidget />);
    // Default category is Forex, so EURUSD is visible and XAUUSD is filtered out.
    await screen.findByText('EURUSD');
    expect(screen.queryByText('XAUUSD')).toBeNull();

    for (const cat of ['Forex', 'Commodities', 'Indices', 'Stocks', 'Cryptocurrencies']) {
      expect(screen.getByText(cat)).toBeTruthy();
    }

    fireEvent.click(screen.getByText('Commodities'));
    expect(screen.getByText('XAUUSD')).toBeTruthy();
    expect(screen.queryByText('EURUSD')).toBeNull();
  });

  it('shows an explicit empty state rather than a silently blank table when a filter matches nothing (FR-UI-034)', async () => {
    marketsMock.mockResolvedValue(directoryPage([], null));

    render(<MarketsWidget />);
    await waitFor(() => expect(screen.getByText('No symbols available for Forex.')).toBeTruthy());
  });

  it('filters the directory to the selected watchlist, restoring the watchlist selector', async () => {
    listMock.mockResolvedValue({
      data: [watchlist({ watchlist_id: 'wl-1', name: 'My Forex List', items: [{ source_id: 'mt5', symbol: 'EURUSD', sort_order: 0 }] })],
    });
    marketsMock.mockResolvedValue(
      directoryPage(
        [
          marketRow({ symbol: 'EURUSD', name: 'EURUSD', asset_class: 'Forex' }),
          marketRow({ symbol: 'GBPUSD', name: 'GBPUSD', asset_class: 'Forex' }),
        ],
        null
      )
    );

    render(<MarketsWidget />);
    await screen.findByText('EURUSD');
    // No watchlist selected by default: the whole (category-filtered) directory shows.
    expect(screen.getByText('GBPUSD')).toBeTruthy();

    await screen.findByText('My Forex List');
    fireEvent.change(screen.getByDisplayValue('All Instruments'), { target: { value: 'wl-1' } });

    await waitFor(() => expect(screen.queryByText('GBPUSD')).toBeNull());
    expect(screen.getByText('EURUSD')).toBeTruthy();
  });

  it('sorts by Symbol, Change, and Volume with a stable symbol tiebreak (FR-UI-035)', async () => {
    marketsMock.mockResolvedValue(
      directoryPage(
        [
          marketRow({ symbol: 'NZDCAD', name: 'NZDCAD', volume: 100, change: 0.001, change_percent: 0.1 }),
          marketRow({ symbol: 'AUDCAD', name: 'AUDCAD', volume: 100, change: 0.002, change_percent: 0.2 }),
          marketRow({ symbol: 'GBPCAD', name: 'GBPCAD', volume: 500, change: -0.05, change_percent: -0.9 }),
        ],
        null
      )
    );

    render(<MarketsWidget />);
    await screen.findByText('AUDCAD');

    const symbolCellsInOrder = () => screen.getAllByRole('row').slice(1).map((row) => row.textContent ?? '');

    // Default sort is Volume; AUDCAD/NZDCAD tie at 100 and must tiebreak
    // alphabetically (AUDCAD before NZDCAD), both behind GBPCAD's 500.
    let rows = symbolCellsInOrder();
    expect(rows[0]).toContain('GBPCAD');
    expect(rows[1]).toContain('AUDCAD');
    expect(rows[2]).toContain('NZDCAD');

    fireEvent.change(screen.getByDisplayValue('Sort by Volume'), { target: { value: 'Symbol' } });
    rows = symbolCellsInOrder();
    expect(rows.map((r) => r.slice(0, 6))).toEqual(['AUDCAD', 'GBPCAD', 'NZDCAD']);
  });

  it('TRADE opens the confirmation ticket when confirmation is required, else submits directly (FR-UI-036)', async () => {
    marketsMock.mockResolvedValue(directoryPage([marketRow()], null));
    render(<MarketsWidget />);
    await screen.findByText('EURUSD');

    fireEvent.click(screen.getByText('TRADE'));
    expect(openOrderTicketMock).toHaveBeenCalledWith({ symbol: 'EURUSD', side: 'BUY', type: 'Market' });
    expect(submitOrderMock).not.toHaveBeenCalled();
  });

  it('TRADE submits immediately when confirmation is disabled (FR-UI-036)', async () => {
    orderConfirmationRequired = false;
    marketsMock.mockResolvedValue(directoryPage([marketRow()], null));
    render(<MarketsWidget />);
    await screen.findByText('EURUSD');

    fireEvent.click(screen.getByText('TRADE'));
    expect(submitOrderMock).toHaveBeenCalledWith({ symbol: 'EURUSD', side: 'BUY', qty: 1, orderType: 'Market' });
    expect(openOrderTicketMock).not.toHaveBeenCalled();
  });

  it('offers Chart and Price Ladder per row, and disables Options everywhere (FR-UI-037)', async () => {
    marketsMock.mockResolvedValue(directoryPage([marketRow()], null));
    render(<MarketsWidget />);
    await screen.findByText('EURUSD');

    fireEvent.click(screen.getByRole('button', { name: '' })); // the MoreVertical row-menu toggle
    expect(screen.getByText('Chart')).toBeTruthy();
    expect(screen.getByText('Price Ladder')).toBeTruthy();
    const optionsItem = screen.getByText('Options').closest('[aria-disabled]');
    expect(optionsItem?.getAttribute('aria-disabled')).toBe('true');

    fireEvent.click(screen.getByText('Options'));
    expect(addWidgetToWorkspaceMock).not.toHaveBeenCalled();

    fireEvent.click(screen.getByText('Chart'));
    expect(addWidgetToWorkspaceMock).toHaveBeenCalledWith('chart', 'EURUSD Chart', 'EURUSD');
  });

  it('renders em dashes instead of inventing unavailable evidence (FR-UI-030/032)', async () => {
    marketsMock.mockResolvedValue(
      directoryPage(
        [marketRow({ change: null, change_percent: null, open: null, high: null, low: null })],
        null
      )
    );

    render(<MarketsWidget />);
    await screen.findByText('EURUSD');

    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
  });
});
