import { beforeEach, expect, it, vi } from 'vitest';
import { filterMt5Symbols, mt5Definitions, mt5ImportRanges, type Mt5ImportRequest } from '../../../../../app/plugins/DataSource/MetaTrader/mt5Import';
import { useMt5Import } from '../../../../../app/plugins/DataSource/MetaTrader/mt5ImportStore';
import * as backend from '../../../../../app/plugins/DataSource/MetaTrader/backend';
vi.mock('../../../../../app/plugins/DataSource/MetaTrader/backend', () => ({ mt5Catalog: vi.fn(), mt5Connect: vi.fn(), mt5Symbols: vi.fn(), mt5Add: vi.fn(), mt5Download: vi.fn(), mt5Status: vi.fn(), mt5Cancel: vi.fn() }));
const symbols = [{ name: 'EURUSD', description: 'Euro', path: 'Forex-Majors', category: 'Forex' }];
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
