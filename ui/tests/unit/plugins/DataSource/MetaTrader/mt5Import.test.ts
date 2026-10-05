import { beforeEach, expect, it, vi } from 'vitest';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { Mt5ImportDialog } from '../../../../../app/plugins/DataSource/MetaTrader/Mt5ImportDialog';
import { filterMt5Symbols, groupMt5Symbols, mt5Definitions, mt5ImportRanges, type Mt5ImportRequest, type Mt5Symbol } from '../../../../../app/plugins/DataSource/MetaTrader/mt5Import';
import { useMt5Import } from '../../../../../app/plugins/DataSource/MetaTrader/mt5ImportStore';
import * as backend from '../../../../../app/plugins/DataSource/MetaTrader/backend';
import { ApiClientError } from '../../../../../app/host/transport';
vi.mock('../../../../../app/plugins/DataSource/MetaTrader/backend', () => ({ mt5Catalog: vi.fn(), mt5Connect: vi.fn(), mt5Symbols: vi.fn(), mt5Add: vi.fn(), mt5Download: vi.fn(), mt5Status: vi.fn(), mt5Cancel: vi.fn() }));
const symbols = [{ name: 'EURUSD', description: 'Euro', path: 'Forex-Majors', category: 'Forex' }];
const categorySymbols: Mt5Symbol[] = [
  { name: 'XAUUSD', description: 'Gold US Dollar', path: 'Markets\\Commodities\\Gold\\XAUUSD', category: 'Markets-Commodities-Gold' },
  { name: 'XAUEUR', description: 'Gold Euro', path: 'Markets\\Commodities\\Gold\\XAUEUR', category: 'Markets-Commodities-Gold' },
  { name: 'EURUSD', description: 'Euro US Dollar', path: 'Markets\\Forex\\Majors\\EURUSD', category: 'Markets-Forex-Majors' },
  { name: 'AUDUSD', description: 'Australian Dollar', path: 'Markets\\Forex\\Majors\\AUDUSD', category: 'Markets-Forex-Majors' },
  { name: 'GOLD_FUTURE', description: 'Gold future', path: 'Markets\\Commodities\\Gold\\Futures\\GOLD_FUTURE', category: 'Markets-Commodities-Gold-Futures' },
  { name: 'UNKNOWN', description: 'No category', path: 'UNKNOWN', category: '' },
  { name: 'NAMED', description: 'Named category', path: 'Uncategorized\\NAMED', category: 'Uncategorized' },
];
const request: Mt5ImportRequest = { folder: '', symbols: ['EURUSD'], dateFrom: '2024-01-01', dateTo: '2024-01-02', dateType: 'custom', broker: '-1', brokerName: 'Default', timezone: 'UTC', postfix: '_MT' };
beforeEach(() => {
  vi.resetAllMocks();
  useMt5Import.setState({ definitions: [], symbols: [], ranges: {}, job: null, backendAvailable: false, storageError: '' });
  vi.mocked(backend.mt5Catalog).mockResolvedValue({ available: true, connected: true, reason: '', datasets: [] });
  vi.mocked(backend.mt5Symbols).mockResolvedValue({ symbols });
});
it('uses only terminal-returned symbols and preserves selected date ranges', () => {
  expect(filterMt5Symbols('eur', '', symbols)).toEqual(symbols);
  expect(filterMt5Symbols('', '', [])).toEqual([]);
  expect(mt5Definitions(request, [], symbols)[0].symbol).toBe('EURUSD_MT');
  expect(mt5Definitions(request, ['EURUSD_MT'], symbols)[0].symbol).toBe('EURUSD_MT_1');
  expect(() => mt5Definitions({ ...request, symbols: ['UNKNOWN'] }, [], symbols)).toThrow('Select symbols');
  expect(mt5ImportRanges(request, symbols).EURUSD).toEqual({ from: '2024-01-01', to: '2024-01-02' });
});
it('keeps actionable prerequisite details and request identity in failed imports', async () => {
  useMt5Import.setState({ backendAvailable: true, symbols });
  vi.mocked(backend.mt5Add).mockResolvedValue({ id: 'a'.repeat(32) });
  vi.mocked(backend.mt5Download).mockRejectedValue(new ApiClientError('CLOCK_SCHEMA_REQUIRED', 'Broker clock setup required', [], 409, 'req-server-123'));
  await expect(useMt5Import.getState().start(request, mt5Definitions(request, [], symbols), false)).rejects.toThrow('request_id=req-server-123');
  expect(useMt5Import.getState().job).toMatchObject({ state: 'failed', error: 'Broker clock setup required [CLOCK_SCHEMA_REQUIRED; request_id=req-server-123]' });
  expect(backend.mt5Status).not.toHaveBeenCalled();
});
it('groups sibling symbols by the supplied parent category and retains raw paths', () => {
  const before = structuredClone(categorySymbols);
  const groups = groupMt5Symbols(categorySymbols);
  expect(groups.map(group => group.label)).toEqual([
    'Markets-Commodities-Gold', 'Markets-Forex-Majors',
    'Markets-Commodities-Gold-Futures', 'Uncategorized', 'Uncategorized',
  ]);
  expect(groups[0].rows.map(row => row.name)).toEqual(['XAUUSD', 'XAUEUR']);
  expect(groups[1].rows.map(row => row.name)).toEqual(['EURUSD', 'AUDUSD']);
  expect(new Set(groups.map(group => group.key)).size).toBe(5);
  expect(categorySymbols).toEqual(before);
});
it('combines exact parent category filtering with name and description search', () => {
  expect(filterMt5Symbols('', 'category:Markets-Commodities-Gold', categorySymbols).map(row => row.name)).toEqual(['XAUUSD', 'XAUEUR']);
  expect(filterMt5Symbols(' EURO ', 'category:Markets-Commodities-Gold', categorySymbols).map(row => row.name)).toEqual(['XAUEUR']);
  expect(filterMt5Symbols('aud', 'category:Markets-Commodities-Gold', categorySymbols)).toEqual([]);
  expect(filterMt5Symbols('', '', categorySymbols)).toEqual(categorySymbols);
  expect(filterMt5Symbols('', 'uncategorized', categorySymbols).map(row => row.name)).toEqual(['UNKNOWN']);
  expect(filterMt5Symbols('', 'category:Uncategorized', categorySymbols).map(row => row.name)).toEqual(['NAMED']);
});
it('preserves long category labels while grouping and filtering their sibling symbols', () => {
  const longCategory = 'Markets-Commodities-Gold-' + 'Long category label '.repeat(15);
  const rows = [
    { name: 'LONG', description: 'Long', path: 'Long\\LONG', category: longCategory },
    { name: 'LONG2', description: 'Long 2', path: 'Long\\LONG2', category: longCategory },
  ];
  const groups = groupMt5Symbols(rows);
  expect(groups).toHaveLength(1);
  expect(groups[0].label).toBe(longCategory);
  expect(filterMt5Symbols('', groups[0].key, [...categorySymbols, ...rows])).toEqual(rows);
});
it('describes the saved global terminal default and retains Fetch symbols', () => {
  const html = renderToStaticMarkup(createElement(Mt5ImportDialog, {
    onClose: () => {}, onStarted: () => {},
  }));
  expect(html).toContain('Use global settings');
  expect(html).toContain('Use enabled global MT5 settings, or enter terminal64.exe path');
  expect(html).toContain('Fetch symbols');
  expect(html).not.toContain('Auto-detect');
  expect(backend.mt5Connect).not.toHaveBeenCalled();
});
it('does not advance imports with timers or create browser datasets', async () => {
  await useMt5Import.getState().connect('');
  expect(backend.mt5Connect).toHaveBeenCalledWith('');
  vi.mocked(backend.mt5Add).mockResolvedValue({ id: 'a'.repeat(32) });
  vi.mocked(backend.mt5Download).mockResolvedValue({ job_id: 'actual-job' });
  await useMt5Import.getState().start(request, mt5Definitions(request, [], symbols), false);
  for (let i = 0; i < 100; i++) useMt5Import.getState().advance();
  expect(useMt5Import.getState().job?.state).toBe('running');
  expect(useMt5Import.getState().definitions).toEqual([]);
  vi.mocked(backend.mt5Status).mockResolvedValue({ state: 'succeeded', rows: 2, progress: 1 });
  vi.mocked(backend.mt5Catalog).mockResolvedValue({ available: true, connected: true, reason: '', datasets: [{ id: 'a'.repeat(32), symbol: 'EURUSD_MT', underlying: 'EURUSD', instrument: 'EURUSD', timeframe: 'M1', broker: '-1', date_from: '2024-01-01', date_to: '2024-01-02', bars: 2, options: { metadata: {} } }] });
  await useMt5Import.getState().poll();
  expect(useMt5Import.getState().job?.state).toBe('completed');
  expect(useMt5Import.getState().definitions[0].bars).toBe(2);
});
it('propagates terminal failures with no catalog fallback', async () => {
  vi.mocked(backend.mt5Connect).mockRejectedValue(new Error('Terminal unavailable'));
  await expect(useMt5Import.getState().connect('')).rejects.toThrow('Terminal unavailable');
  expect(backend.mt5Symbols).not.toHaveBeenCalled();
  expect(useMt5Import.getState().symbols).toEqual([]);
  await expect(useMt5Import.getState().start(request, mt5Definitions(request, [], symbols), false)).rejects.toThrow('unavailable');
});

it('loads broker profiles from catalog and populates postfix on request', async () => {
  const brokers = [
    { id: '2', name: 'RoboForex', postfix: '_roboforex', timezone: 'EET', mtUse: true, instruments: [] },
    { id: '4', name: 'Darwinex', postfix: '_darwinex', timezone: 'EETUS', mtUse: true, instruments: [] },
  ];
  vi.mocked(backend.mt5Catalog).mockResolvedValue({ available: true, connected: true, reason: '', datasets: [], brokers });
  await useMt5Import.getState().refresh();
  expect(useMt5Import.getState().brokers).toEqual(brokers);

  const roboReq: Mt5ImportRequest = {
    ...request,
    broker: brokers[0].id,
    brokerName: brokers[0].name,
    timezone: brokers[0].timezone,
    postfix: brokers[0].postfix,
  };
  const defs = mt5Definitions(roboReq, [], symbols);
  expect(defs[0].symbol).toBe('EURUSD_roboforex');
  expect(defs[0].broker).toBe('2');
  // Verify start succeeds with non-UTC timezone (e.g. EET / EETUS) without throwing
  await useMt5Import.getState().connect('');
  vi.mocked(backend.mt5Add).mockResolvedValue({ id: 'b'.repeat(32) });
  vi.mocked(backend.mt5Download).mockResolvedValue({ job_id: 'job-robo' });
  await useMt5Import.getState().start(roboReq, defs, false);
  expect(useMt5Import.getState().job?.state).toBe('running');
  expect(useMt5Import.getState().postfix).toBe('_roboforex');
});

it('handles canonical datasets from catalog without crashing and marks backend available', async () => {
  const canonicalDataset = {
    id: 'canon-1',
    symbol: 'EURUSD',
    source: 'MT5',
    underlying: 'EURUSD',
    instrument: 'EURUSD',
    timeframe: 'M1',
    broker: '-1',
    brokerName: 'Default',
    timezone: 'UTC',
    from: '2024-01-01',
    to: '2024-06-01',
    bars: 5000,
  };
  vi.mocked(backend.mt5Catalog).mockResolvedValue({
    available: true,
    connected: false,
    reason: '',
    datasets: [canonicalDataset as any],
    brokers: [],
  });
  await useMt5Import.getState().refresh();
  expect(useMt5Import.getState().backendAvailable).toBe(true);
  expect(useMt5Import.getState().storageError).toBe('');
  expect(useMt5Import.getState().definitions.length).toBe(1);
  expect(useMt5Import.getState().definitions[0].id).toBe('canon-1');
  expect(useMt5Import.getState().definitions[0].from).toBe('2024-01-01');
  expect(useMt5Import.getState().definitions[0].to).toBe('2024-06-01');
});
