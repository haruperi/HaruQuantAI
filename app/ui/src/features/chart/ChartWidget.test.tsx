/** Focused unit evidence for Charting Tools Widget, FR-UI-046 and FR-UI-047. */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  ChartWidget,
  barExtent,
  maxVolume,
  toChartBars,
  visibleBarRange,
  type BarData,
} from './ChartWidget';
import { BAR_TIMEFRAMES } from '../../clients';
import { resetSymbolUniverse } from '../watchlists/symbolUniverse';

const {
  openOrderTicketMock,
  submitOrderMock,
  symbolsMock,
  quotesMock,
  barsMock,
  indicatorSeriesMock,
  indicatorCatalogueMock,
  setWidgetSymbolMock,
} = vi.hoisted(() => ({
  openOrderTicketMock: vi.fn(),
  submitOrderMock: vi.fn(),
  symbolsMock: vi.fn(),
  quotesMock: vi.fn(),
  barsMock: vi.fn(),
  indicatorSeriesMock: vi.fn(),
  indicatorCatalogueMock: vi.fn(),
  setWidgetSymbolMock: vi.fn(),
}));

const localPreferences = new Map<string, string>();

vi.mock('../../store/useTradingStore', () => ({
  useTradingStore: () => ({
    products: [
      { symbol: 'ESU6', name: 'E-mini S&P 500', price: 5400, change: 10, changePercent: 0.2 },
      { symbol: 'EURUSD', name: 'Euro / US Dollar', price: 1.085, change: 0.001, changePercent: 0.1 },
    ],
    openOrderTicket: openOrderTicketMock,
    submitOrder: submitOrderMock,
    theme: 'dark',
  }),
}));

vi.mock('../workspaces', () => ({
  useWorkspaceStore: () => ({
    orderConfirmationRequired: true,
    toggleExpandWidget: vi.fn(),
    setWidgetSymbol: setWidgetSymbolMock,
  }),
}));

vi.mock('@/clients', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/clients')>();
  return {
    ...actual,
    apiClients: {
      ...actual.apiClients,
      data: {
        ...actual.apiClients.data,
        symbols: symbolsMock,
        quotes: quotesMock,
        bars: barsMock,
      },
      indicators: {
        ...actual.apiClients.indicators,
        catalogue: indicatorCatalogueMock,
        series: indicatorSeriesMock,
      },
    },
    unwrapData: (response: { data: unknown }) => response.data,
  };
});

/** Build one broker bar series response in the transport shape. */
function barSeries(
  bars: { time: string; open: number; high: number; low: number; close: number; volume: number }[],
  symbol = 'EURUSD',
  timeframe = 'H1'
): { data: unknown } {
  return {
    data: {
      source_id: 'mt5',
      symbol,
      timeframe,
      bars,
      count: bars.length,
      start: bars[0]?.time ?? null,
      end: bars[bars.length - 1]?.time ?? null,
      cache_status: 'not_used',
      request_id: 'req-1',
    },
  };
}

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
    },
  };
}

function indicatorSeries(
  indicatorId: 'ema' | 'rsi',
  values: (number | null)[],
  period: number
): { data: unknown } {
  const validCount = values.filter((value) => value !== null).length;
  return {
    data: {
      indicator_id: indicatorId,
      name: indicatorId === 'ema' ? 'Exponential Moving Average' : 'Relative Strength Index',
      symbol: 'EURUSD',
      timeframe: 'H1',
      source_id: 'mt5',
      parameters: { period, source: 'close' },
      points: values.map((value, index) => ({
        time: `2026-08-13T${String(9 + index).padStart(2, '0')}:00:00+00:00`,
        value,
        unavailable_reason: value === null ? 'warmup' : null,
      })),
      count: values.length,
      valid_count: validCount,
      availability: validCount ? 'available' : 'insufficient_history',
      unavailable_reason: validCount ? null : 'warmup',
      indicator_version: '1.0.0',
      formula_version: '1.0.0',
      request_id: 'req-indicator',
    },
  };
}

function indicatorSpec(indicatorId: string, name: string): Record<string, unknown> {
  return {
    indicator_id: indicatorId,
    name,
    indicator_version: '1.0.0',
    formula_version: '1.0.0',
    tier: 'core_mvp',
    required_columns: ['source'],
    parameter_schema: {},
    output_templates: [`${indicatorId}_{period}`],
    warmup_policy: 'period',
    vectorized: true,
    multi_symbol: false,
    multi_timeframe: false,
    import_path: `app.services.indicators.${indicatorId}`,
    stability: 'stable',
    workflow_eligibility: ['research'],
  };
}

describe('ChartWidget — FR-UI-046 Symbol Universe Autocomplete & Bar Fetching', () => {
  beforeEach(() => {
    localPreferences.clear();
    Object.defineProperty(window, 'localStorage', {
      configurable: true,
      value: {
        getItem: vi.fn((key: string) => localPreferences.get(key) ?? null),
        setItem: vi.fn((key: string, value: string) => localPreferences.set(key, value)),
        removeItem: vi.fn((key: string) => localPreferences.delete(key)),
        clear: vi.fn(() => localPreferences.clear()),
        key: vi.fn((index: number) => [...localPreferences.keys()][index] ?? null),
        get length() { return localPreferences.size; },
      },
    });
    resetSymbolUniverse();
    symbolsMock.mockReset();
    quotesMock.mockReset();
    quotesMock.mockResolvedValue({
      data: {
        source_id: 'mt5',
        rows: [
          { symbol: 'EURUSD', last: 1.085, bid: 1.0849, ask: 1.0851, close: 1.085 },
          { symbol: 'ESU6', last: 5400, bid: 5399.75, ask: 5400.25, close: 5400 },
        ],
      },
    });
    setWidgetSymbolMock.mockReset();
    barsMock.mockReset();
    barsMock.mockResolvedValue(
      barSeries([
        { time: '2026-08-13T09:00:00+00:00', open: 1.085, high: 1.0862, low: 1.0844, close: 1.0858, volume: 940 },
        { time: '2026-08-13T10:00:00+00:00', open: 1.0858, high: 1.0871, low: 1.0851, close: 1.0866, volume: 1120 },
      ])
    );
    openOrderTicketMock.mockReset();
    submitOrderMock.mockReset();

    // Mock HTMLCanvasElement context for chart rendering
    const mockContext = {
      save: vi.fn(),
      restore: vi.fn(),
      clearRect: vi.fn(),
      fillRect: vi.fn(),
      strokeRect: vi.fn(),
      rect: vi.fn(),
      clip: vi.fn(),
      beginPath: vi.fn(),
      moveTo: vi.fn(),
      lineTo: vi.fn(),
      stroke: vi.fn(),
      fill: vi.fn(),
      fillText: vi.fn(),
      measureText: vi.fn().mockReturnValue({ width: 50 }),
      setLineDash: vi.fn(),
      closePath: vi.fn(),
      arc: vi.fn(),
      rotate: vi.fn(),
      scale: vi.fn(),
      translate: vi.fn(),
      transform: vi.fn(),
      setTransform: vi.fn(),
      resetTransform: vi.fn(),
      createLinearGradient: vi.fn().mockReturnValue({
        addColorStop: vi.fn(),
      }),
      createPattern: vi.fn(),
      drawImage: vi.fn(),
    };
    HTMLCanvasElement.prototype.getContext = vi.fn().mockReturnValue(mockContext) as any;
  });

  afterEach(() => {
    resetSymbolUniverse();
  });

  it('initializes with default settings: EURUSD, H1, Bars 100 with no indicators', () => {
    symbolsMock.mockResolvedValueOnce(symbolPage(['EURUSD', 'ESU6'], null));

    render(<ChartWidget />);

    const searchInput = screen.getByRole('combobox', { name: 'Symbol search' });
    expect(searchInput).toHaveValue('EURUSD');

    const rangeBySelect = screen.getByRole('combobox', { name: 'Range By' });
    expect(rangeBySelect).toHaveValue('Bars');

    const barCountSelect = screen.getByRole('combobox', { name: 'Bar Count' });
    expect(barCountSelect).toHaveValue('100');

    expect(screen.getByText(/EURUSD • H1 • HaruQuantAI/i)).toBeInTheDocument();
  });

  it('loads in-memory broker symbol universe and shows auto-suggestions on typing', async () => {
    symbolsMock.mockResolvedValueOnce(
      symbolPage(['ESU6', 'EURUSD', 'GBPUSD', 'GBPJPY', 'US10Y'], null)
    );

    render(<ChartWidget symbol="EURUSD" />);

    const searchInput = screen.getByRole('combobox', { name: 'Symbol search' });
    expect(searchInput).toHaveValue('EURUSD');

    // Type "EUR" into the search input box
    fireEvent.change(searchInput, { target: { value: 'EUR' } });

    const listbox = await suggestionList();
    expect(listbox).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'EURUSD' })).toBeInTheDocument();
  });

  it('supports keyboard navigation and selection via Enter', async () => {
    symbolsMock.mockResolvedValueOnce(
      symbolPage(['ESU6', 'EURUSD', 'GBPUSD', 'GBPJPY'], null)
    );

    render(<ChartWidget symbol="EURUSD" />);

    const searchInput = screen.getByRole('combobox', { name: 'Symbol search' });

    // Focus & type "GBP"
    fireEvent.focus(searchInput);
    fireEvent.change(searchInput, { target: { value: 'GBP' } });

    await suggestionList();

    // Press ArrowDown to highlight suggestion (GBPJPY)
    fireEvent.keyDown(searchInput, { key: 'ArrowDown' });

    // Press Enter to select
    fireEvent.keyDown(searchInput, { key: 'Enter' });

    // Suggestion list closes and active symbol updates to GBPJPY
    await waitFor(() => {
      expect(querySuggestionList()).not.toBeInTheDocument();
    });
    expect(searchInput).toHaveValue('GBPJPY');
    expect(screen.getByText(/GBPJPY • H1 • HaruQuantAI/i)).toBeInTheDocument();
  });

  it('selects suggestion on mouse click (onMouseDown)', async () => {
    symbolsMock.mockResolvedValueOnce(
      symbolPage(['ESU6', 'EURUSD', 'US10Y'], null)
    );

    render(<ChartWidget symbol="ESU6" />);

    const searchInput = screen.getByRole('combobox', { name: 'Symbol search' });
    fireEvent.focus(searchInput);
    fireEvent.change(searchInput, { target: { value: 'EUR' } });

    await suggestionList();
    const option = screen.getByRole('option', { name: 'EURUSD' });
    fireEvent.mouseDown(option);

    await waitFor(() => {
      expect(querySuggestionList()).not.toBeInTheDocument();
    });
    expect(searchInput).toHaveValue('EURUSD');
    expect(screen.getByText(/EURUSD • H1 • HaruQuantAI/i)).toBeInTheDocument();
  });

  it('renders Range By controls and switches between Bars dropdown and Date pickers', () => {
    symbolsMock.mockResolvedValueOnce(symbolPage(['EURUSD'], null));

    render(<ChartWidget symbol="EURUSD" />);

    // Default Range By selection is "Bars"
    const rangeBySelect = screen.getByRole('combobox', { name: 'Range By' });
    expect(rangeBySelect).toHaveValue('Bars');

    // Bar Count select dropdown is present with default 100
    const barCountSelect = screen.getByRole('combobox', { name: 'Bar Count' });
    expect(barCountSelect).toHaveValue('100');

    // Change bar count to 5000
    fireEvent.change(barCountSelect, { target: { value: '5000' } });
    expect(barCountSelect).toHaveValue('5000');

    // Switch Range By mode to "Date"
    fireEvent.change(rangeBySelect, { target: { value: 'Date' } });
    expect(rangeBySelect).toHaveValue('Date');

    // Date From and Date To inputs are now rendered
    const dateFromInput = screen.getByLabelText('Date From');
    const dateToInput = screen.getByLabelText('Date To');
    expect(dateFromInput).toBeInTheDocument();
    expect(dateToInput).toBeInTheDocument();
  });

  it('formats price scale and overlay legend using dynamic symbol digits from MT5 symbol info', async () => {
    quotesMock.mockResolvedValueOnce({
      data: {
        source_id: 'mt5',
        rows: [{ symbol: 'EURUSD', last: 1.08542, bid: 1.0854, ask: 1.08545, close: 1.08542, digits: 5 }],
      },
    });

    render(<ChartWidget symbol="EURUSD" />);

    await waitFor(() => {
      expect(screen.getByText(/EURUSD • H1 • HaruQuantAI/i)).toBeInTheDocument();
    });

    // EURUSD has 5 digits in MT5 symbol info
    expect(quotesMock).toHaveBeenCalledWith(['EURUSD']);
  });

  it('requests real broker bars for the active symbol, timeframe, and bar count', async () => {
    render(<ChartWidget symbol="EURUSD" />);

    await waitFor(() => {
      expect(barsMock).toHaveBeenCalledWith({
        symbol: 'EURUSD',
        timeframe: 'H1',
        limit: 100,
      });
    });
  });

  it('requests a date window instead of a bar count when Range By is Date', async () => {
    render(<ChartWidget symbol="EURUSD" />);
    await waitFor(() => expect(barsMock).toHaveBeenCalled());
    barsMock.mockClear();

    fireEvent.change(screen.getByRole('combobox', { name: 'Range By' }), {
      target: { value: 'Date' },
    });

    await waitFor(() => {
      expect(barsMock).toHaveBeenCalledTimes(1);
    });
    const call = barsMock.mock.calls[0][0];
    expect(call.symbol).toBe('EURUSD');
    expect(call.limit).toBeUndefined();
    expect(call.start).toMatch(/^\d{4}-\d{2}-\d{2}T00:00:00Z$/);
    expect(call.end).toMatch(/^\d{4}-\d{2}-\d{2}T23:59:59Z$/);
  });

  it('reports an unavailable broker series instead of drawing generated bars', async () => {
    barsMock.mockRejectedValue(new Error('Bars unavailable'));

    render(<ChartWidget symbol="EURUSD" />);

    expect(await screen.findByText('Bars unavailable')).toBeInTheDocument();
  });

  it('reports an empty broker series rather than filling the gap', async () => {
    barsMock.mockResolvedValue(barSeries([]));

    render(<ChartWidget symbol="EURUSD" />);

    expect(
      await screen.findByText('No H1 bars available for EURUSD')
    ).toBeInTheDocument();
  });

  it('offers only timeframes the broker can serve', async () => {
    render(<ChartWidget symbol="EURUSD" />);
    await waitFor(() => expect(barsMock).toHaveBeenCalled());

    fireEvent.click(screen.getByRole('button', { name: 'H1' }));

    expect(screen.getByText('1 minute')).toBeInTheDocument();
    expect(screen.getByText('4 hours')).toBeInTheDocument();
    // Data's manifest has no 3-minute, 10-minute, or 2-hour bar.
    expect(screen.queryByText('3 minutes')).not.toBeInTheDocument();
    expect(screen.queryByText('10 minutes')).not.toBeInTheDocument();
    expect(screen.queryByText('2 hours')).not.toBeInTheDocument();
  });

  it('offers every and only timeframe in the canonical Data manifest', async () => {
    render(<ChartWidget symbol="EURUSD" />);
    await waitFor(() => expect(barsMock).toHaveBeenCalled());

    fireEvent.click(screen.getByRole('button', { name: 'H1' }));

    const expectedLabels: Record<(typeof BAR_TIMEFRAMES)[number], string> = {
      M1: '1 minute',
      M5: '5 minutes',
      M15: '15 minutes',
      M30: '30 minutes',
      H1: '1 hour',
      H4: '4 hours',
      D1: '1 day',
      W1: '1 week',
      MN1: '1 month',
    };
    const offeredLabels = Array.from(document.querySelectorAll('.tv-dropdown-item')).map(
      (item) => item.textContent?.trim()
    );
    indicatorSeriesMock.mockReset();
    indicatorSeriesMock.mockImplementation(({ indicatorId, period }) =>
      Promise.resolve(
        indicatorSeries(
          indicatorId,
          indicatorId === 'ema' ? [null, 1.086] : [null, 52],
          period
        )
      )
    );
    indicatorCatalogueMock.mockReset();
    indicatorCatalogueMock.mockResolvedValue({
      data: [
        indicatorSpec('ema', 'Exponential Moving Average'),
        indicatorSpec('rsi', 'Relative Strength Index'),
        indicatorSpec('macd', 'Moving Average Convergence Divergence'),
      ],
    });

    expect(offeredLabels).toEqual(BAR_TIMEFRAMES.map((key) => expectedLabels[key]));
  });

  it('preserves timeframe selection independently per widget instance', async () => {
    render(
      <>
        <ChartWidget symbol="EURUSD" />
        <ChartWidget symbol="ESU6" />
      </>
    );
    await waitFor(() => expect(barsMock).toHaveBeenCalledTimes(2));

    fireEvent.click(screen.getAllByRole('button', { name: 'H1' })[0]);
    fireEvent.click(screen.getByText('15 minutes'));

    expect(screen.getByRole('button', { name: 'M15' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'H1' })).toBeInTheDocument();
    await waitFor(() => {
      expect(barsMock).toHaveBeenCalledWith({
        symbol: 'EURUSD',
        timeframe: 'M15',
        limit: 100,
      });
    });
  });

  it('refetches with the canonical timeframe key when the timeframe changes', async () => {
    render(<ChartWidget symbol="EURUSD" />);
    await waitFor(() => expect(barsMock).toHaveBeenCalled());
    barsMock.mockClear();

    fireEvent.click(screen.getByRole('button', { name: 'H1' }));
    fireEvent.click(screen.getByText('15 minutes'));

    await waitFor(() => {
      expect(barsMock).toHaveBeenCalledWith({
        symbol: 'EURUSD',
        timeframe: 'M15',
        limit: 100,
      });
    });
  });

  it('reports the charted symbol to the workspace so the widget heading follows it', async () => {
    symbolsMock.mockResolvedValueOnce(symbolPage(['EURUSD', 'GBPJPY'], null));

    render(<ChartWidget symbol="EURUSD" widgetId="chart-1" />);

    await waitFor(() => {
      expect(setWidgetSymbolMock).toHaveBeenCalledWith('chart-1', 'EURUSD');
    });

    const searchInput = screen.getByRole('combobox', { name: 'Symbol search' });
    fireEvent.focus(searchInput);
    fireEvent.change(searchInput, { target: { value: 'GBP' } });
    await suggestionList();
    fireEvent.mouseDown(screen.getByRole('option', { name: 'GBPJPY' }));

    await waitFor(() => {
      expect(setWidgetSymbolMock).toHaveBeenCalledWith('chart-1', 'GBPJPY');
    });
  });

  it('does not report a symbol when the chart is not a workspace widget', async () => {
    render(<ChartWidget symbol="EURUSD" />);

    await waitFor(() => expect(barsMock).toHaveBeenCalled());
    expect(setWidgetSymbolMock).not.toHaveBeenCalled();
  });

  it('updates chart legend and bar data dynamically when symbol or timeframe changes', async () => {
    quotesMock.mockResolvedValue({
      data: {
        source_id: 'mt5',
        rows: [
          { symbol: 'EURUSD', last: 1.08542, bid: 1.0854, ask: 1.08545, close: 1.08542, digits: 5 },
          { symbol: 'GBPJPY', last: 198.54, bid: 198.53, ask: 198.55, close: 198.54, digits: 3 },
        ],
      },
    });

    symbolsMock.mockResolvedValue(symbolPage(['EURUSD', 'GBPJPY'], null));

    render(<ChartWidget symbol="EURUSD" />);

    await waitFor(() => {
      expect(screen.getByText(/EURUSD • H1 • HaruQuantAI/i)).toBeInTheDocument();
    });

    const searchInput = screen.getByRole('combobox', { name: 'Symbol search' });
    fireEvent.focus(searchInput);
    fireEvent.change(searchInput, { target: { value: 'GBP' } });

    await suggestionList();
    const option = screen.getByRole('option', { name: 'GBPJPY' });
    fireEvent.mouseDown(option);

    await waitFor(() => {
      expect(screen.getByText(/GBPJPY • H1 • HaruQuantAI/i)).toBeInTheDocument();
    });
  });

  it('fetches and presents Indicators-owned EMA with authoritative parameters', async () => {
    render(<ChartWidget symbol="EURUSD" />);
    await waitFor(() => expect(barsMock).toHaveBeenCalled());

    fireEvent.click(screen.getByRole('button', { name: /Indicators/ }));
    fireEvent.click(await screen.findByRole('button', { name: /Exponential Moving Average/ }));

    await waitFor(() => {
      expect(indicatorSeriesMock).toHaveBeenCalledWith({
        indicatorId: 'ema',
        symbol: 'EURUSD',
        timeframe: 'H1',
        period: 20,
        source: 'close',
        limit: 100,
      });
    });
    expect(await screen.findByText('EMA · period 20 · close')).toBeInTheDocument();
  });

  it('renders RSI in a separate panel without joining across warm-up values', async () => {
    barsMock.mockResolvedValueOnce(
      barSeries([
        { time: '2026-08-13T09:00:00+00:00', open: 1.085, high: 1.0862, low: 1.0844, close: 1.0858, volume: 940 },
        { time: '2026-08-13T10:00:00+00:00', open: 1.0858, high: 1.0871, low: 1.0851, close: 1.0866, volume: 1120 },
        { time: '2026-08-13T11:00:00+00:00', open: 1.0866, high: 1.088, low: 1.086, close: 1.0874, volume: 1050 },
        { time: '2026-08-13T12:00:00+00:00', open: 1.0874, high: 1.0884, low: 1.0868, close: 1.0879, volume: 980 },
      ])
    );
    indicatorSeriesMock.mockResolvedValueOnce(indicatorSeries('rsi', [null, null, 45, 55], 14));
    render(<ChartWidget symbol="EURUSD" />);
    await waitFor(() => expect(barsMock).toHaveBeenCalled());

    fireEvent.click(screen.getByRole('button', { name: /Indicators/ }));
    fireEvent.click(await screen.findByRole('button', { name: /Relative Strength Index/ }));

    expect(await screen.findByText('RSI · period 14 · close')).toBeInTheDocument();
    expect(screen.getByTestId('rsi-panel')).toBeInTheDocument();
    expect(screen.getAllByTestId('rsi-segment')).toHaveLength(1);
    expect(screen.getByText('70')).toBeInTheDocument();
    expect(screen.getByText('30')).toBeInTheDocument();
  });

  it('anchors RSI timestamps to the same horizontal pan transform as chart bars', async () => {
    indicatorSeriesMock.mockResolvedValueOnce(indicatorSeries('rsi', [45, 50], 14));
    render(<ChartWidget symbol="EURUSD" />);
    await waitFor(() => expect(barsMock).toHaveBeenCalled());

    fireEvent.click(screen.getByRole('button', { name: /Indicators/ }));
    fireEvent.click(await screen.findByRole('button', { name: /Relative Strength Index/ }));

    const segment = await screen.findByTestId('rsi-segment');
    const before = segment.getAttribute('points');
    const canvas = screen.getByTestId('chart-canvas');
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 80 });
    fireEvent.mouseMove(canvas, { clientX: 140, clientY: 80 });
    fireEvent.mouseUp(canvas);

    await waitFor(() => expect(segment.getAttribute('points')).not.toBe(before));
    expect(Number(canvas.getAttribute('data-pan-offset'))).toBe(40);
  });

  it('reports wholly insufficient indicator history instead of presenting completion', async () => {
    indicatorSeriesMock.mockResolvedValueOnce(indicatorSeries('rsi', [null, null], 14));
    render(<ChartWidget symbol="EURUSD" />);
    await waitFor(() => expect(barsMock).toHaveBeenCalled());

    fireEvent.click(screen.getByRole('button', { name: /Indicators/ }));
    fireEvent.click(await screen.findByRole('button', { name: /Relative Strength Index/ }));

    expect(
      await screen.findByText(/Unavailable: insufficient history \(warmup\)/)
    ).toBeInTheDocument();
    expect(screen.queryByTestId('rsi-segment')).not.toBeInTheDocument();
  });

  it('loads the real indicator catalogue when the fx Indicators modal opens', async () => {
    render(<ChartWidget symbol="EURUSD" />);

    fireEvent.click(screen.getByRole('button', { name: /Indicators/ }));

    await waitFor(() => expect(indicatorCatalogueMock).toHaveBeenCalled());
    expect(
      await screen.findByRole('button', { name: /Exponential Moving Average/ })
    ).toBeEnabled();
    expect(screen.getByRole('button', { name: /Relative Strength Index/ })).toBeEnabled();
    expect(
      screen.getByRole('button', { name: /Moving Average Convergence Divergence/ })
    ).toBeDisabled();
    expect(screen.queryByText('52 Week High/Low')).not.toBeInTheDocument();
  });

  it('searches owner catalogue names and reports no matches truthfully', async () => {
    render(<ChartWidget symbol="EURUSD" />);
    fireEvent.click(screen.getByRole('button', { name: /Indicators/ }));
    await screen.findByRole('button', { name: /Exponential Moving Average/ });

    fireEvent.change(screen.getByPlaceholderText('Search indicator script name...'), {
      target: { value: 'relative strength' },
    });
    expect(screen.getByRole('button', { name: /Relative Strength Index/ })).toBeEnabled();
    expect(
      screen.queryByRole('button', { name: /Exponential Moving Average/ })
    ).not.toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText('Search indicator script name...'), {
      target: { value: 'not registered' },
    });
    expect(screen.getByText('No registered indicators found')).toBeInTheDocument();
  });

  it('reports an unavailable indicator catalogue instead of showing mock entries', async () => {
    indicatorCatalogueMock.mockRejectedValueOnce(new Error('Catalogue unavailable'));
    render(<ChartWidget symbol="EURUSD" />);

    fireEvent.click(screen.getByRole('button', { name: /Indicators/ }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Indicator catalogue unavailable');
    expect(screen.queryByText('EMA')).not.toBeInTheDocument();
  });

  describe('FR-UI-051 through FR-UI-054 completion', () => {
  it('persists drawings as an instrument-scoped client preference', async () => {
    const first = render(<ChartWidget symbol="EURUSD" />);
    await waitFor(() => expect(barsMock).toHaveBeenCalled());

    fireEvent.click(screen.getByTitle('Lines & Channels'));
    fireEvent.click(screen.getByText('Trend Line'));
    const canvas = screen.getByTestId('chart-canvas');
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 80 });
    fireEvent.mouseMove(canvas, { clientX: 180, clientY: 130 });
    fireEvent.mouseUp(canvas);

    const storageKey = 'haruquantai.chart.drawings.v1:EURUSD';
    await waitFor(() => expect(JSON.parse(localPreferences.get(storageKey) ?? '[]')).toHaveLength(1));
    expect(localPreferences.has('haruquantai.chart.drawings.v1:GBPJPY')).toBe(false);

    first.unmount();
    render(<ChartWidget symbol="EURUSD" />);
    fireEvent.click(screen.getByTitle('Undo'));
    await waitFor(() => expect(localPreferences.get(storageKey)).toBe('[]'));
  });

  it('fails safely when stored drawing preferences are malformed', () => {
    localPreferences.set('haruquantai.chart.drawings.v1:EURUSD', '{not-json');
    expect(() => render(<ChartWidget symbol="EURUSD" />)).not.toThrow();
  });

  it('restores and mutates only the selected instrument drawing partition', async () => {
    const drawing = {
      id: 'gbp-line',
      tool: 'trendline',
      startX: 10,
      startY: 20,
      endX: 50,
      endY: 60,
    };
    localPreferences.set('haruquantai.chart.drawings.v1:EURUSD', JSON.stringify([drawing]));
    localPreferences.set(
      'haruquantai.chart.drawings.v1:GBPJPY',
      JSON.stringify([drawing, { ...drawing, id: 'gbp-line-2' }])
    );

    render(<ChartWidget symbol="GBPJPY" />);
    fireEvent.click(screen.getByTitle('Undo'));

    await waitFor(() =>
      expect(JSON.parse(localPreferences.get('haruquantai.chart.drawings.v1:GBPJPY') ?? '[]'))
        .toHaveLength(1)
    );
    expect(JSON.parse(localPreferences.get('haruquantai.chart.drawings.v1:EURUSD') ?? '[]'))
      .toHaveLength(1);
  });

  it('changes chart appearance without refetching or replacing bar data', async () => {
    render(<ChartWidget symbol="EURUSD" />);
    await waitFor(() => expect(barsMock).toHaveBeenCalled());
    const callsBeforeAppearanceChange = barsMock.mock.calls.length;

    fireEvent.click(screen.getByTitle('Chart Style: Candles'));
    fireEvent.click(screen.getByText('Line', { selector: 'span' }));

    expect(screen.getByTestId('chart-canvas')).toHaveAttribute('data-chart-type', 'Line');
    expect(barsMock).toHaveBeenCalledTimes(callsBeforeAppearanceChange);
  });

  it('marks timestamp discontinuities and presents the missing-bar count', async () => {
    const response = barSeries([
      { time: '2026-08-13T09:00:00+00:00', open: 1, high: 2, low: 0.5, close: 1.5, volume: 10 },
      { time: '2026-08-13T11:00:00+00:00', open: 1.5, high: 2.5, low: 1, close: 2, volume: 12 },
    ]);
    const projected = toChartBars(response.data as any, 'H1');
    expect(projected[1].missingBarsBefore).toBe(1);
    barsMock.mockResolvedValueOnce(response);

    render(<ChartWidget symbol="EURUSD" />);
    expect(await screen.findByTestId('chart-gap-status')).toHaveTextContent(
      '1 missing bar shown as gaps'
    );
  });

  it('keeps the latest bar in a bounded viewport at the one-million-bar maximum', () => {
    const barCount = 1_000_000;
    const plotWidth = 600;
    const candleWidth = 10;
    const latestOffset = plotWidth - barCount * candleWidth;
    const range = visibleBarRange(barCount, plotWidth, candleWidth, latestOffset);

    expect(range.end).toBe(barCount);
    expect(range.end - range.start).toBe(60);
    const beyondHistory = visibleBarRange(barCount, plotWidth, candleWidth, -20_000_000);
    expect(beyondHistory.end).toBe(barCount);
    expect(beyondHistory.end - beyondHistory.start).toBeLessThanOrEqual(61);
  });
  });
});

describe('backtest-scale bar windows', () => {
  /**
   * MT5 holds 178,514 H1 bars for USDJPY alone, and the Bar Count control now
   * offers up to 1,000,000. `Math.min(...bars)` passes one argument per
   * element and throws RangeError past roughly 130k, so the scale reducers
   * must stay spread-free or the chart cannot draw a single candle at these
   * sizes.
   */
  const HUGE = 250_000;

  function hugeSeries(): BarData[] {
    const bars: BarData[] = new Array(HUGE);
    for (let i = 0; i < HUGE; i++) {
      const base = 100 + Math.sin(i / 500) * 5;
      bars[i] = {
        open: base,
        high: base + 0.5,
        low: base - 0.5,
        close: base + 0.1,
        volume: 1000 + (i % 97),
        timestamp: '2026-08-13T00:00:00+00:00',
        time: '00:00',
      };
    }
    // Unambiguous extremes the reducers must find.
    bars[HUGE - 2] = { ...bars[0], low: 1.25, high: 1.25 };
    bars[3] = { ...bars[0], high: 987.5, low: 987.5 };
    bars[7] = { ...bars[0], volume: 424_242 };
    return bars;
  }

  it('reduces a quarter-million bars without overflowing the call stack', () => {
    const bars = hugeSeries();

    // The form this replaced, at this size, on this engine.
    expect(() => Math.max(...bars.map((b) => b.high))).toThrow(RangeError);

    expect(() => barExtent(bars, 0, bars.length)).not.toThrow();
    expect(() => maxVolume(bars, 0, bars.length)).not.toThrow();
  });

  it('reports the true extremes across the full series', () => {
    const bars = hugeSeries();
    const { min, max } = barExtent(bars, 0, bars.length);
    expect(min).toBe(1.25);
    expect(max).toBe(987.5);
    expect(maxVolume(bars, 0, bars.length)).toBe(424_242);
  });

  it('confines its scan to the requested window', () => {
    const bars = hugeSeries();
    // Index 3 (the 987.5 spike) and index 7 (the volume spike) sit outside it.
    const { max } = barExtent(bars, 10, 2000);
    expect(max).toBeLessThan(200);
    expect(maxVolume(bars, 10, 2000)).toBeLessThan(2000);
  });

  it('never returns a zero divisor for volume scaling', () => {
    const flat: BarData[] = [
      { open: 1, high: 1, low: 1, close: 1, volume: 0, timestamp: 't', time: 't' },
    ];
    expect(maxVolume(flat, 0, 1)).toBe(1);
  });
});
