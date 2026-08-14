/** Focused unit evidence for Markets (FEAT-UI-02), FR-UI-030 through FR-UI-037. */

import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { MarketsWidget } from './MarketsWidget';
import { WATCHLISTS_CHANGED_EVENT } from '../watchlists/watchlistEvents';

const { marketsMock, quotesMock, snapshotStreamMock, listMock, openOrderTicketMock, submitOrderMock, addWidgetToWorkspaceMock } = vi.hoisted(() => ({
  marketsMock: vi.fn(),
  quotesMock: vi.fn(),
  snapshotStreamMock: vi.fn(),
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
    data: { markets: marketsMock, quotes: quotesMock, snapshotStream: snapshotStreamMock },
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
    quotesMock.mockResolvedValue(directoryPage([marketRow()], null));
    snapshotStreamMock.mockImplementation(async function* () {});
  });

  afterEach(() => {
    Object.defineProperty(document, 'visibilityState', { configurable: true, value: 'visible' });
    cleanup();
    vi.clearAllMocks();
  });

  it('reads the market directory, not a watchlist, with no client-elected source_id (FR-UI-033)', async () => {
    marketsMock.mockResolvedValue(directoryPage([marketRow()], null));

    render(<MarketsWidget streamSettlingMs={0} />);
    await screen.findByText('EURUSD');

    expect(marketsMock).toHaveBeenCalledWith({ limit: 50, cursor: undefined, includeTechnicals: true });
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

    render(<MarketsWidget streamSettlingMs={0} />);
    await waitFor(() => expect(marketsMock).toHaveBeenCalledTimes(4));

    // Wait for the zero-duration injected settling clock to flush, then confirm
    // a 5th page was never requested despite next_cursor never being null.
    await waitFor(() => expect(snapshotStreamMock).toHaveBeenCalledTimes(1));
    expect(marketsMock).toHaveBeenCalledTimes(4);
    expect(screen.getAllByRole('row').length).toBeGreaterThan(1); // header + >=1 data row
  });

  it('starts streaming only after initial loading and the settling delay', async () => {
    let resolveMarkets!: (value: { data: unknown }) => void;
    marketsMock.mockReturnValue(
      new Promise((resolve) => {
        resolveMarkets = resolve;
      })
    );

    render(<MarketsWidget streamSettlingMs={50} />);
    expect(snapshotStreamMock).not.toHaveBeenCalled();

    resolveMarkets(directoryPage([marketRow()], null));
    await screen.findByText('EURUSD');
    expect(screen.getByText(/Streaming starts in/)).toBeInTheDocument();
    expect(snapshotStreamMock).not.toHaveBeenCalled();

    await waitFor(() => expect(snapshotStreamMock).toHaveBeenCalledTimes(1));
  });

  it('pauses when hidden and resumes without reloading initial market data', async () => {
    marketsMock.mockResolvedValue(directoryPage([marketRow()], null));
    snapshotStreamMock.mockImplementation(
      (_symbols: string[], options: { signal: AbortSignal }) => (async function* () {
        await new Promise<void>((resolve) => {
          options.signal.addEventListener('abort', () => resolve(), { once: true });
        });
      })()
    );

    render(<MarketsWidget streamSettlingMs={0} />);
    await waitFor(() => expect(snapshotStreamMock).toHaveBeenCalledTimes(1));

    Object.defineProperty(document, 'visibilityState', { configurable: true, value: 'hidden' });
    fireEvent(document, new Event('visibilitychange'));
    await waitFor(() => {
      const firstSignal = snapshotStreamMock.mock.calls[0][1].signal as AbortSignal;
      expect(firstSignal.aborted).toBe(true);
    });

    Object.defineProperty(document, 'visibilityState', { configurable: true, value: 'visible' });
    fireEvent(document, new Event('visibilitychange'));
    await waitFor(() => expect(snapshotStreamMock).toHaveBeenCalledTimes(2));
    expect(marketsMock).toHaveBeenCalledTimes(1);
  });

  it('surfaces a load failure explicitly rather than an empty table (FR-UI-032)', async () => {
    marketsMock.mockRejectedValue(new Error('network'));

    render(<MarketsWidget streamSettlingMs={0} />);
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

    render(<MarketsWidget streamSettlingMs={0} />);
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

    render(<MarketsWidget streamSettlingMs={0} />);
    await waitFor(() => expect(screen.getByText('No symbols available for Forex.')).toBeTruthy());
  });

  it('filters the directory to the selected watchlist, defaulting to the default watchlist on load', async () => {
    listMock.mockResolvedValue({
      data: [
        watchlist({ watchlist_id: 'wl-1', name: 'Default List', is_default: true, items: [{ source_id: 'mt5', symbol: 'EURUSD', sort_order: 0 }] }),
        watchlist({ watchlist_id: 'wl-2', name: 'Cable List', is_default: false, items: [{ source_id: 'mt5', symbol: 'GBPUSD', sort_order: 0 }] }),
      ],
    });
    quotesMock.mockImplementation((symbols: string[]) => {
      if (symbols.includes('EURUSD')) {
        return Promise.resolve(directoryPage([marketRow({ symbol: 'EURUSD', name: 'EURUSD', asset_class: 'Forex' })], null));
      }
      return Promise.resolve(directoryPage([marketRow({ symbol: 'GBPUSD', name: 'GBPUSD', asset_class: 'Forex' })], null));
    });

    render(<MarketsWidget />);
    await screen.findByText('EURUSD');

    // Default watchlist is selected automatically on load; GBPUSD (not in wl-1) is filtered out.
    await screen.findByText('Default List (default)');
    await waitFor(() => expect(screen.queryByText('GBPUSD')).toBeNull());
    expect(screen.getByText('EURUSD')).toBeTruthy();
    expect(screen.queryByText('All Instruments')).toBeNull();

    // Selecting another watchlist ("Cable List") filters to its symbols.
    fireEvent.change(screen.getByDisplayValue('Default List (default)'), { target: { value: 'wl-2' } });
    await waitFor(() => expect(screen.getByText('GBPUSD')).toBeTruthy());
    expect(screen.queryByText('EURUSD')).toBeNull();
  });

  it('dynamically renders asset class tabs according to the active watchlist', async () => {
    listMock.mockResolvedValue({
      data: [
        watchlist({
          watchlist_id: 'wl-single',
          name: 'Forex Only',
          is_default: true,
          items: [{ source_id: 'mt5', symbol: 'EURUSD', asset_class: 'Forex', sort_order: 0 }],
        }),
        watchlist({
          watchlist_id: 'wl-multi',
          name: 'Multi Asset',
          is_default: false,
          items: [
            { source_id: 'mt5', symbol: 'EURUSD', asset_class: 'Forex', sort_order: 0 },
            { source_id: 'mt5', symbol: 'XAUUSD', asset_class: 'Commodities', sort_order: 1 },
          ],
        }),
      ],
    });
    quotesMock.mockImplementation((symbols: string[]) => {
      const rows = [];
      if (symbols.includes('EURUSD')) rows.push(marketRow({ symbol: 'EURUSD', name: 'EURUSD', asset_class: 'Forex' }));
      if (symbols.includes('XAUUSD')) rows.push(marketRow({ symbol: 'XAUUSD', name: 'XAUUSD', asset_class: 'Commodities' }));
      return Promise.resolve(directoryPage(rows, null));
    });

    render(<MarketsWidget />);
    await screen.findByText('EURUSD');

    // For single-class watchlist, only the Forex category pill tab is rendered.
    expect(screen.getByText('Forex')).toBeTruthy();
    expect(screen.queryByText('Commodities')).toBeNull();

    // Switching to multi-class watchlist renders both Forex and Commodities tabs.
    fireEvent.change(screen.getByDisplayValue('Forex Only (default)'), { target: { value: 'wl-multi' } });
    await waitFor(() => expect(screen.getByText('Commodities')).toBeTruthy());
    expect(screen.getByText('Forex')).toBeTruthy();

    // Clicking Commodities tab filters displayed symbols to Commodities.
    fireEvent.click(screen.getByText('Commodities'));
    await waitFor(() => expect(screen.getByText('XAUUSD')).toBeTruthy());
    expect(screen.queryByText('EURUSD')).toBeNull();
  });

  it('reloads demand when another widget changes the active watchlist (FR-UI-192)', async () => {
    listMock
      .mockResolvedValueOnce({
        data: [watchlist({ items: [{ source_id: 'mt5', symbol: 'EURUSD', sort_order: 0 }] })],
      })
      .mockResolvedValueOnce({
        data: [watchlist({ items: [{ source_id: 'mt5', symbol: 'GBPUSD', sort_order: 0 }] })],
      });
    quotesMock.mockImplementation((symbols: string[]) =>
      Promise.resolve(directoryPage(symbols.map((symbol) => marketRow({ symbol, name: symbol })), null))
    );
    render(<MarketsWidget streamSettlingMs={0} />);
    await screen.findByText('EURUSD');

    window.dispatchEvent(new Event(WATCHLISTS_CHANGED_EVENT));

    await screen.findByText('GBPUSD');
    await waitFor(() => expect(snapshotStreamMock).toHaveBeenLastCalledWith(
      ['GBPUSD'],
      expect.objectContaining({ signal: expect.any(AbortSignal) })
    ));
  });

  it('sorts by Symbol, Change, Volatility, ADR, and Range with a stable symbol tiebreak (FR-UI-035)', async () => {
    marketsMock.mockResolvedValue(
      directoryPage(
        [
          marketRow({ symbol: 'NZDCAD', name: 'NZDCAD', change_percent: 0.1, volatility: 0.001, adr: 0.005, high: 1.1, low: 1.05 }),
          marketRow({ symbol: 'AUDCAD', name: 'AUDCAD', change_percent: 0.2, volatility: 0.003, adr: 0.002, high: 1.2, low: 1.05 }),
          marketRow({ symbol: 'GBPCAD', name: 'GBPCAD', change_percent: -0.9, volatility: 0.002, adr: 0.01, high: 1.3, low: 1.0 }),
        ],
        null
      )
    );

    render(<MarketsWidget />);
    await screen.findByText('AUDCAD');

    const symbolCellsInOrder = () => screen.getAllByRole('row').slice(1).map((row) => row.textContent ?? '');

    // Default sort is Symbol
    let rows = symbolCellsInOrder();
    expect(rows.map((r) => r.slice(0, 6))).toEqual(['AUDCAD', 'GBPCAD', 'NZDCAD']);

    // Sort by Change (GBPCAD |-0.9%| > AUDCAD |0.2%| > NZDCAD |0.1%|)
    fireEvent.change(screen.getByDisplayValue('Symbol'), { target: { value: 'Change' } });
    rows = symbolCellsInOrder();
    expect(rows[0]).toContain('GBPCAD');

    // Sort by Volatility (AUDCAD 0.003 > GBPCAD 0.002 > NZDCAD 0.001)
    fireEvent.change(screen.getByDisplayValue('Change'), { target: { value: 'Volatility' } });
    rows = symbolCellsInOrder();
    expect(rows[0]).toContain('AUDCAD');

    // Sort by ADR (GBPCAD 0.01 > NZDCAD 0.005 > AUDCAD 0.002)
    fireEvent.change(screen.getByDisplayValue('Volatility'), { target: { value: 'ADR' } });
    rows = symbolCellsInOrder();
    expect(rows[0]).toContain('GBPCAD');

    // Sort by Range (GBPCAD 0.3 > AUDCAD 0.15 > NZDCAD 0.05)
    fireEvent.change(screen.getByDisplayValue('ADR'), { target: { value: 'Range' } });
    rows = symbolCellsInOrder();
    expect(rows[0]).toContain('GBPCAD');
  });

  it('applies color-coding to the Range column according to threshold rules', async () => {
    marketsMock.mockResolvedValue(
      directoryPage(
        [
          marketRow({ symbol: 'SYM1', name: 'SYM1', range_percent_of_adr: 35.0 }),   // Green <= 40 Safe
          marketRow({ symbol: 'SYM2', name: 'SYM2', range_percent_of_adr: 55.0 }),   // Blue <= 60 Mandatory
          marketRow({ symbol: 'SYM3', name: 'SYM3', range_percent_of_adr: 75.0 }),   // Yellow <= 80 Caution
          marketRow({ symbol: 'SYM4', name: 'SYM4', range_percent_of_adr: 95.0 }),   // Orange <= 100 Warning
          marketRow({ symbol: 'SYM5', name: 'SYM5', range_percent_of_adr: 115.0 }),  // Red > 100 Danger
        ],
        null
      )
    );

    render(<MarketsWidget />);
    await screen.findByText('35.0%');

    expect(screen.getByText('35.0%').style.color).toBe('rgb(0, 228, 115)');   // #00e473
    expect(screen.getByText('55.0%').style.color).toBe('rgb(41, 182, 246)');   // #29b6f6
    expect(screen.getByText('75.0%').style.color).toBe('rgb(255, 202, 40)');   // #ffca28
    expect(screen.getByText('95.0%').style.color).toBe('rgb(255, 152, 0)');    // #ff9800
    expect(screen.getByText('115.0%').style.color).toBe('rgb(255, 0, 61)');   // #ff003d
  });

  it('shows Bid as Last Price, unavailable initial Age, and Spread in integer points (FR-UI-030)', async () => {
    marketsMock.mockResolvedValue(directoryPage([marketRow({ last: 9.99999 })], null));

    render(<MarketsWidget />);
    const row = (await screen.findByText('EURUSD')).closest('tr');
    expect(row).not.toBeNull();

    const cells = within(row!).getAllByRole('cell');
    expect(cells[1]).toHaveTextContent('1.10490');
    expect(cells[2]).toHaveTextContent('—');
    expect(cells[3]).toHaveTextContent('20');
    const headers = screen.getAllByRole('columnheader').map((header) => header.textContent);
    expect(headers.slice(0, 4)).toEqual(['Symbol', 'Last Price', 'Age', 'Spread']);
    expect(screen.getByRole('columnheader', { name: 'Spread' })).toBeInTheDocument();
    expect(screen.queryByRole('columnheader', { name: 'Bid' })).toBeNull();
    expect(screen.queryByRole('columnheader', { name: 'Ask' })).toBeNull();
    expect(screen.queryByRole('columnheader', { name: 'Status' })).toBeNull();
  });

  it('converts three-digit spread evidence to integer MT5 points (FR-UI-030)', async () => {
    marketsMock.mockResolvedValue(
      directoryPage([marketRow({ symbol: 'USDJPY', name: 'USDJPY', digits: 3, spread: 0.006 })], null)
    );

    render(<MarketsWidget />);
    const row = (await screen.findByText('USDJPY')).closest('tr');
    expect(within(row!).getAllByRole('cell')[3]).toHaveTextContent('6');
  });

  it('keeps invalid live quote time explicit (FR-UI-030)', async () => {
    marketsMock.mockResolvedValue(directoryPage([marketRow()], null));
    snapshotStreamMock.mockImplementation((_symbols: string[], options: { signal: AbortSignal }) => (async function* () {
      yield {
        sequence: 1,
        payload: {
          quotes: [{ symbol: 'EURUSD', bid: '1.20001', ask: '1.20002', spread: '0.00001', digits: 5, time: 'invalid' }],
          stale: false,
          gap: 0,
        },
      };
      await new Promise<void>((resolve) => options.signal.addEventListener('abort', () => resolve(), { once: true }));
    })());

    render(<MarketsWidget streamSettlingMs={0} />);
    const liveButton = await screen.findByRole('button', { name: 'Trade EURUSD; quote status: live' });
    const cells = within(liveButton.closest('tr')!).getAllByRole('cell');
    expect(cells[2]).toHaveTextContent('—');
    expect(cells[3]).toHaveTextContent('1');
  });

  it('keeps unavailable initial spread explicit (FR-UI-030)', async () => {
    marketsMock.mockResolvedValue(directoryPage([marketRow({ spread: null })], null));
    render(<MarketsWidget />);
    const row = (await screen.findByText('EURUSD')).closest('tr');
    expect(within(row!).getAllByRole('cell')[3]).toHaveTextContent('—');
  });

  it('colors Trade green for live, yellow for stale, and red when not live (FR-UI-030/036)', async () => {
    marketsMock.mockResolvedValue(directoryPage([marketRow()], null));
    snapshotStreamMock.mockImplementation((_symbols: string[], options: { signal: AbortSignal }) => (async function* () {
      yield {
        sequence: 1,
        payload: {
          quotes: [{
            symbol: 'EURUSD',
            bid: '1.20001',
            ask: '1.20007',
            spread: '0.00006',
            digits: 5,
            time: new Date(Date.now() - 6_000).toISOString(),
          }],
          stale: false,
          gap: 0,
        },
      };
      await new Promise<void>((resolve) => options.signal.addEventListener('abort', () => resolve(), { once: true }));
    })());

    const liveView = render(<MarketsWidget streamSettlingMs={0} />);
    const liveButton = await screen.findByRole('button', { name: 'Trade EURUSD; quote status: live' });
    expect(liveButton.style.color).toBe('rgb(0, 228, 115)');
    expect(screen.getByText('1.20001')).toBeInTheDocument();
    const liveRow = screen.getByText('EURUSD').closest('tr');
    const liveCells = within(liveRow!).getAllByRole('cell');
    expect(liveCells[2]).toHaveTextContent('6s');
    expect(liveCells[3]).toHaveTextContent('6');
    expect(liveCells[4]).toHaveTextContent('+0.00500 (+0.45%)');
    expect(liveCells[8]).toHaveTextContent('1.10000');
    expect(liveCells[9]).toHaveTextContent('1.10800');
    expect(liveCells[10]).toHaveTextContent('1.10500');
    liveView.unmount();

    snapshotStreamMock.mockImplementation((_symbols: string[], options: { signal: AbortSignal }) => (async function* () {
      yield {
        sequence: 2,
        payload: {
          quotes: [{ symbol: 'EURUSD', bid: '1.20002', ask: '1.20004', spread: '0.00002' }],
          stale: true,
          gap: 0,
        },
      };
      await new Promise<void>((resolve) => options.signal.addEventListener('abort', () => resolve(), { once: true }));
    })());
    const staleView = render(<MarketsWidget streamSettlingMs={0} />);
    const staleButton = await screen.findByRole('button', { name: 'Trade EURUSD; quote status: stale' });
    expect(staleButton.style.color).toBe('rgb(255, 202, 40)');
    staleView.unmount();

    snapshotStreamMock.mockImplementation(async function* () {});
    render(<MarketsWidget streamSettlingMs={0} />);
    const offlineButton = await screen.findByRole('button', { name: 'Trade EURUSD; quote status: not live' });
    expect(offlineButton.style.color).toBe('rgb(255, 0, 61)');
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

  it('formats populated volatility, ADR, and range evidence from the API', async () => {
    marketsMock.mockResolvedValue(
      directoryPage(
        [
          marketRow({ volatility: 0.125, adr: 50, range_percent_of_adr: 60 }),
          marketRow({
            symbol: 'AUDCAD',
            volatility: 0.0825,
            adr: 44.4,
            range_percent_of_adr: 72.1,
          }),
        ],
        null
      )
    );

    render(<MarketsWidget />);
    await screen.findByText('EURUSD');
    await screen.findByText('AUDCAD');

    expect(screen.getByText('12.50%')).toBeTruthy();
    expect(screen.getByText('50.0')).toBeTruthy();
    expect(screen.getByText('60.0%')).toBeTruthy();
    expect(screen.getByText('8.25%')).toBeTruthy();
    expect(screen.getByText('44.4')).toBeTruthy();
    expect(screen.getByText('72.1%')).toBeTruthy();
  });
});
