/** Focused unit evidence for Watchlists (FEAT-UI-12). */

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { WatchlistWidget } from './WatchlistWidget';

const { createMock, listMock, quotesMock, removeMock, updateMock } = vi.hoisted(
  () => ({
    createMock: vi.fn(),
    listMock: vi.fn(),
    quotesMock: vi.fn(),
    removeMock: vi.fn(),
    updateMock: vi.fn(),
  })
);

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
    data: { quotes: quotesMock },
  },
  unwrapData: (response: { data: unknown }) => response.data,
}));

const defaultList = {
  watchlist_id: 'wl-default',
  account_id: 'acct-1',
  name: 'default',
  is_default: true,
  sort_order: 0,
  items: [{ source_id: 'mt5', symbol: 'EURUSD', sort_order: 0 }],
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
    listMock.mockResolvedValue({ data: [defaultList, customList] });
    quotesMock.mockResolvedValue({
      data: {
        rows: [{ symbol: 'EURUSD', name: 'EURUSD', last: 1.1 }],
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
  });

  it('loads and selects the default watchlist', async () => {
    render(<WatchlistWidget />);

    await screen.findByText('EURUSD');
    expect((screen.getByRole('combobox') as HTMLSelectElement).value).toBe(
      'wl-default'
    );
    expect(listMock).toHaveBeenCalledOnce();
    expect(quotesMock).toHaveBeenCalledWith(['EURUSD']);
  });

  it('delegates create, rename, default, and item mutations', async () => {
    render(<WatchlistWidget />);
    const selector = await screen.findByRole('combobox');

    fireEvent.change(selector, { target: { value: 'wl-custom' } });
    fireEvent.click(screen.getByText('CREATE NEW'));
    fireEvent.change(screen.getByPlaceholderText('Watchlist name…'), {
      target: { value: 'New List' },
    });
    fireEvent.click(screen.getByText('Save'));
    await waitFor(() => expect(createMock).toHaveBeenCalledWith('New List'));

    fireEvent.change(screen.getByRole('combobox'), {
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
    fireEvent.change(await screen.findByRole('combobox'), {
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
});
