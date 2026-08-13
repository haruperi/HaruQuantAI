/** Focused unit evidence for Watchlists (FEAT-UI-03), FR-UI-038 through FR-UI-044. */

import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { WatchlistWidget } from './WatchlistWidget';
import { resetSymbolUniverse } from './symbolUniverse';

const { createMock, listMock, quotesMock, removeMock, symbolsMock, updateMock } =
  vi.hoisted(() => ({
    createMock: vi.fn(),
    listMock: vi.fn(),
    quotesMock: vi.fn(),
    removeMock: vi.fn(),
    symbolsMock: vi.fn(),
    updateMock: vi.fn(),
  }));

vi.mock('../../store/useTradingStore', () => ({
  useTradingStore: () => ({
    openOrderTicket: vi.fn(),
    submitOrder: vi.fn(),
  }),
}));

vi.mock('../workspaces', () => ({
  useWorkspaceStore: () => ({
    orderConfirmationRequired: true,
    addWidgetToWorkspace: vi.fn(),
  }),
}));

vi.mock('@/clients', () => ({
  apiClients: {
    watchlists: {
      create: createMock,
      list: listMock,
      remove: removeMock,
      update: updateMock,
    },
    data: { quotes: quotesMock, symbols: symbolsMock },
  },
  unwrapData: (response: { data: unknown }) => response.data,
}));

/** The autocomplete popup. Scoped because `<select>` children are options too. */
function suggestionList(): Promise<HTMLElement> {
  return screen.findByRole('listbox', { name: 'Symbol suggestions' });
}

function querySuggestionList(): HTMLElement | null {
  return screen.queryByRole('listbox', { name: 'Symbol suggestions' });
}

function symbolPage(items: string[], nextCursor: string | null): { data: unknown } {
  return {
    data: {
      source_id: 'mt5',
      items,
      limit: 200,
      next_cursor: nextCursor,
      revision: '1.0.0',
      request_id: 'req-1',
    },
  };
}

const GENERATED_AT = '2026-08-12T00:00:00.000Z';

const defaultList = {
  watchlist_id: 'wl-default',
  account_id: 'acct-1',
  name: 'default',
  is_default: true,
  sort_order: 0,
  items: [{ source_id: 'mt5', symbol: 'EURUSD', sort_order: 0, asset_class: 'Forex' }],
  created_at: '2026-08-12T00:00:00Z',
  updated_at: '2026-08-12T00:00:00Z',
};

const customList = {
  ...defaultList,
  watchlist_id: 'wl-custom',
  name: 'Swing',
  is_default: false,
  sort_order: 1,
  items: [],
};

describe('WatchlistWidget', () => {
  beforeEach(() => {
    resetSymbolUniverse();
    symbolsMock.mockResolvedValue(
      symbolPage(['EURUSD', 'EURGBP', 'GBPUSD', 'XAUEUR', 'USDJPY'], null)
    );
    listMock.mockResolvedValue({ data: [defaultList, customList] });
    quotesMock.mockResolvedValue({
      data: {
        rows: [{ symbol: 'EURUSD', name: 'EURUSD', last: 1.1 }],
        generated_at: GENERATED_AT,
      },
    });
    createMock.mockResolvedValue({ data: { ...customList, watchlist_id: 'wl-new' } });
    updateMock.mockImplementation((_id: string, values: Record<string, unknown>) =>
      Promise.resolve({ data: { ...customList, ...values } })
    );
    removeMock.mockResolvedValue({ data: null });
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  it('loads and selects the default watchlist', async () => {
    render(<WatchlistWidget />);

    await waitFor(() => expect(screen.getByText('EURUSD')).toBeTruthy());
    expect((screen.getByRole('combobox', { name: 'Select watchlist' }) as HTMLSelectElement).value).toBe(
      'wl-default'
    );
    expect(listMock).toHaveBeenCalledOnce();
    expect(screen.getAllByRole('columnheader').map((cell) => cell.textContent)).toEqual([
      'Symbol',
      'Class',
      'Management',
    ]);
    expect(screen.getByText('Forex')).toBeTruthy();
    expect(screen.queryByText('ADD CLASS')).toBeNull();
    expect(screen.queryByRole('combobox', { name: 'Select asset class to add' })).toBeNull();
  });

  it('delegates create, rename, default, and item mutations', async () => {
    render(<WatchlistWidget />);
    const selector = await screen.findByRole('combobox', { name: 'Select watchlist' });

    fireEvent.change(selector, { target: { value: 'wl-custom' } });
    fireEvent.click(screen.getByText('CREATE NEW'));
    fireEvent.change(screen.getByPlaceholderText('Watchlist name…'), {
      target: { value: 'New List' },
    });
    fireEvent.click(screen.getByText('Save'));
    await waitFor(() => expect(createMock).toHaveBeenCalledWith('New List'));

    fireEvent.change(screen.getByRole('combobox', { name: 'Select watchlist' }), {
      target: { value: 'wl-custom' },
    });
    fireEvent.click(screen.getByTitle('Rename watchlist'));
    fireEvent.change(screen.getByDisplayValue('Swing'), {
      target: { value: 'Renamed' },
    });
    fireEvent.click(screen.getByText('Save'));
    await waitFor(() =>
      expect(updateMock).toHaveBeenCalledWith('wl-custom', { name: 'Renamed' })
    );

    fireEvent.change(screen.getByPlaceholderText('Add symbol…'), {
      target: { value: 'GBPUSD' },
    });
    fireEvent.click(screen.getByText('ADD'));
    await waitFor(() =>
      expect(updateMock).toHaveBeenCalledWith('wl-custom', {
        symbols: ['GBPUSD'],
      })
    );

    fireEvent.click(screen.getByTitle('Set as default'));
    await waitFor(() =>
      expect(updateMock).toHaveBeenCalledWith('wl-custom', { is_default: true })
    );
  });

  it('deletes a selected non-default watchlist', async () => {
    render(<WatchlistWidget />);
    fireEvent.change(await screen.findByRole('combobox', { name: 'Select watchlist' }), {
      target: { value: 'wl-custom' },
    });

    fireEvent.click(screen.getByTitle('Delete watchlist'));

    await waitFor(() => expect(removeMock).toHaveBeenCalledWith('wl-custom'));
  });

  it('shows API failures without reporting success', async () => {
    listMock.mockRejectedValueOnce(new Error('unavailable'));
    render(<WatchlistWidget />);

    expect(await screen.findAllByText('Unable to load watchlists.')).toHaveLength(2);
    expect(screen.queryByText('EURUSD')).toBeNull();
  });

  it('marks only symbols absent from the complete in-memory universe as not tradable (FR-UI-042)', async () => {
    listMock.mockResolvedValue({
      data: [
        {
          ...defaultList,
          items: [
            { source_id: 'mt5', symbol: 'EURUSD', sort_order: 0 },
            { source_id: 'mt5', symbol: 'GHOSTFX', sort_order: 1 },
          ],
        },
      ],
    });

    render(<WatchlistWidget />);
    await screen.findByText('GHOSTFX');

    await waitFor(() => expect(screen.getByText('NOT TRADABLE')).toBeTruthy());
    const eurusdRow = screen.getByText('EURUSD').closest('tr');
    expect(eurusdRow?.textContent).not.toContain('NOT TRADABLE');
  });

  it('reorders symbols through the registered update operation (FR-UI-043)', async () => {
    listMock.mockResolvedValue({
      data: [
        {
          ...defaultList,
          items: [
            { source_id: 'mt5', symbol: 'EURUSD', sort_order: 0 },
            { source_id: 'mt5', symbol: 'GBPUSD', sort_order: 1 },
          ],
        },
      ],
    });

    render(<WatchlistWidget />);
    await screen.findByText('GBPUSD');

    fireEvent.click(screen.getAllByTitle('Move down')[0]);
    await waitFor(() =>
      expect(updateMock).toHaveBeenCalledWith('wl-default', { symbols: ['GBPUSD', 'EURUSD'] })
    );
  });

  it('sorts by symbol column with a stable tiebreak (FR-UI-044)', async () => {
    listMock.mockResolvedValue({
      data: [
        {
          ...defaultList,
          items: [
            { source_id: 'mt5', symbol: 'NZDCAD', sort_order: 0 },
            { source_id: 'mt5', symbol: 'AUDCAD', sort_order: 1 },
            { source_id: 'mt5', symbol: 'GBPCAD', sort_order: 2 },
          ],
        },
      ],
    });

    render(<WatchlistWidget />);
    await screen.findByText('GBPCAD');

    const symbolOfRow = (row: HTMLElement) => row.textContent?.slice(0, 6) ?? '';
    const dataRows = () => screen.getAllByRole('row').slice(1);

    fireEvent.click(screen.getByTitle('Sort by Symbol'));
    let ordered = dataRows().map(symbolOfRow);
    expect(ordered).toEqual(['AUDCAD', 'GBPCAD', 'NZDCAD']);

    fireEvent.click(screen.getByTitle('Sort by Symbol'));
    ordered = dataRows().map(symbolOfRow);
    expect(ordered).toEqual(['NZDCAD', 'GBPCAD', 'AUDCAD']);
  });

  it('disables reordering while a column sort is active', async () => {
    listMock.mockResolvedValue({
      data: [
        {
          ...defaultList,
          items: [
            { source_id: 'mt5', symbol: 'EURUSD', sort_order: 0 },
            { source_id: 'mt5', symbol: 'GBPUSD', sort_order: 1 },
          ],
        },
      ],
    });

    render(<WatchlistWidget />);
    await screen.findByText('GBPUSD');

    fireEvent.click(screen.getByTitle('Sort by Symbol'));
    expect(screen.getAllByTitle('Move down')[0]).toBeDisabled();
  });

  it('suggests matching broker symbols as the user types, prefix matches first', async () => {
    render(<WatchlistWidget />);
    await screen.findByText('EURUSD');
    await waitFor(() => expect(symbolsMock).toHaveBeenCalled());

    fireEvent.change(screen.getByPlaceholderText('Add symbol…'), { target: { value: 'eur' } });

    const options = within(await suggestionList()).getAllByRole('option');
    // EURGBP is a new prefix match; XAUEUR is a substring match. EURUSD is
    // already in the selected watchlist, so it is not actionable.
    expect(options.map((option) => option.textContent)).toEqual([
      'EURGBP',
      'XAUEUR',
    ]);
    expect(options.map((option) => option.textContent)).not.toContain('USDJPY');
  });

  it('adds the symbol chosen from the suggestion list', async () => {
    render(<WatchlistWidget />);
    await screen.findByText('EURUSD');
    await waitFor(() => expect(symbolsMock).toHaveBeenCalled());

    fireEvent.change(screen.getByPlaceholderText('Add symbol…'), { target: { value: 'gbp' } });
    fireEvent.mouseDown(within(await suggestionList()).getByRole('option', { name: 'GBPUSD' }));

    await waitFor(() =>
      expect(updateMock).toHaveBeenCalledWith('wl-default', { symbols: ['EURUSD', 'GBPUSD'] })
    );
    expect(querySuggestionList()).toBeNull();
  });

  it('commits the highlighted suggestion on Enter', async () => {
    render(<WatchlistWidget />);
    await screen.findByText('EURUSD');
    await waitFor(() => expect(symbolsMock).toHaveBeenCalled());

    const input = screen.getByPlaceholderText('Add symbol…');
    fireEvent.change(input, { target: { value: 'eur' } });
    await suggestionList();

    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'Enter' });

    // First suggestion is EURGBP, not the raw "eur" the user typed.
    await waitFor(() =>
      expect(updateMock).toHaveBeenCalledWith('wl-default', { symbols: ['EURUSD', 'EURGBP'] })
    );
  });

  it('walks every directory page so the whole broker universe is searchable', async () => {
    symbolsMock.mockReset();
    symbolsMock
      .mockResolvedValueOnce(symbolPage(['EURUSD'], '1'))
      .mockResolvedValueOnce(symbolPage(['ZARJPY'], null));

    render(<WatchlistWidget />);
    await screen.findByText('EURUSD');
    await waitFor(() => expect(symbolsMock).toHaveBeenCalledTimes(2));
    expect(symbolsMock).toHaveBeenLastCalledWith({ limit: 200, cursor: '1' });

    fireEvent.change(screen.getByPlaceholderText('Add symbol…'), { target: { value: 'zar' } });
    expect(within(await suggestionList()).getByRole('option', { name: 'ZARJPY' })).toBeTruthy();
  });

  it('fails closed when the symbol universe cannot be read', async () => {
    symbolsMock.mockRejectedValue(new Error('unavailable'));
    render(<WatchlistWidget />);
    await screen.findByText('EURUSD');

    fireEvent.change(screen.getByPlaceholderText('Add symbol…'), { target: { value: 'GBPUSD' } });
    expect(querySuggestionList()).toBeNull();

    await waitFor(() => expect(screen.getByText('ADD')).toBeDisabled());
    expect(screen.getByRole('alert')).toHaveTextContent(
      'Symbol directory unavailable. Cannot verify instruments.'
    );
    expect(updateMock).not.toHaveBeenCalled();
  });

  it('fails closed when source pagination does not complete within the cap', async () => {
    symbolsMock.mockResolvedValue(symbolPage(['EURUSD'], 'still-more'));
    render(<WatchlistWidget />);
    await screen.findByText('EURUSD');

    await waitFor(() => expect(symbolsMock).toHaveBeenCalledTimes(100));
    expect(screen.getByRole('alert')).toHaveTextContent(
      'Symbol directory unavailable. Cannot verify instruments.'
    );
    expect(screen.getByText('ADD')).toBeDisabled();
  });

  it('rejects typed text that is not an exact source symbol', async () => {
    render(<WatchlistWidget />);
    await screen.findByText('EURUSD');
    await waitFor(() => expect(symbolsMock).toHaveBeenCalled());

    const input = screen.getByRole('combobox', { name: 'Add symbol' });
    fireEvent.change(input, { target: { value: 'gbp' } });
    fireEvent.click(screen.getByText('ADD'));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Select an exact symbol from the connected source.'
    );
    expect(updateMock).not.toHaveBeenCalled();
  });

  it('preserves the exact provider casing and suffix', async () => {
    symbolsMock.mockResolvedValue(symbolPage(['EURUSD', 'Ger40.cash'], null));
    render(<WatchlistWidget />);
    await screen.findByText('EURUSD');
    await waitFor(() => expect(symbolsMock).toHaveBeenCalled());

    const input = screen.getByRole('combobox', { name: 'Add symbol' });
    fireEvent.change(input, { target: { value: 'ger40.cash' } });
    fireEvent.click(screen.getByText('ADD'));

    await waitFor(() =>
      expect(updateMock).toHaveBeenCalledWith('wl-default', {
        symbols: ['EURUSD', 'Ger40.cash'],
      })
    );
  });
});
