import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  discoverMt5Folder,
  filterMt5Symbols,
  mt5Definitions,
  mt5ImportRanges,
  mt5Preset,
  mt5Symbols,
  type Mt5ImportRequest,
} from '../../../../../app/plugins/data_source/MetaTrader/mt5Import';

const request: Mt5ImportRequest = {
  folder: 'MockMT5',
  symbols: ['EURUSD', 'AAPL'],
  dateFrom: '2025-01-01',
  dateTo: '2025-02-01',
  dateType: 'custom',
  broker: '-1',
  brokerName: 'Default',
  timezone: 'UTC',
  postfix: '_MT5',
};

describe('MT5 import rules', () => {
  it('recognizes bounded MT5 folder metadata without reading file contents', () => {
    expect(discoverMt5Folder(['MockMT5/terminal64.exe', 'MockMT5/MQL5/Profiles/a.ini']))
      .toEqual({ folder: 'MockMT5', fileCount: 2 });
    expect(() => discoverMt5Folder([])).toThrow('Select an MT5');
    expect(() => discoverMt5Folder(['Files/readme.txt'])).toThrow('does not look');
    expect(() => discoverMt5Folder(['MT5/../terminal64.exe'])).toThrow('Invalid');
    expect(() => discoverMt5Folder(['MT5/terminal64.exe', 'Other/MQL5/a.ini'])).toThrow('one MT5');
  });

  it('sorts, filters, groups and creates M1 definitions with HaruQuantAI duplicate numbering', () => {
    expect(mt5Symbols).toEqual([...mt5Symbols].sort((a, b) => a.path.localeCompare(b.path) || a.name.localeCompare(b.name)));
    expect(filterMt5Symbols('apple', '')).toMatchObject([{ name: 'AAPL', path: 'Stocks\\US' }]);
    expect(filterMt5Symbols('', 'Forex\\Majors').map(row => row.name)).toEqual(['EURUSD', 'GBPUSD', 'USDJPY']);
    expect(mt5Definitions(request, ['EURUSD_MT5', 'EURUSD_MT5_1'])).toMatchObject([
      { id: 'mt5:EURUSD_MT5_2', symbol: 'EURUSD_MT5_2', timeframe: 'M1', source: 'MT5' },
      { id: 'mt5:AAPL_MT5', symbol: 'AAPL_MT5', timeframe: 'M1', source: 'MT5' },
    ]);
  });

  it('validates ranges and resolves presets against fixture availability', () => {
    expect(mt5ImportRanges(request).EURUSD).toEqual({ from: '2025-01-01', to: '2025-02-01' });
    expect(mt5ImportRanges({ ...request, symbols: ['AAPL'], dateFrom: '2010-01-01', dateType: 'allTime' }).AAPL.from).toBe('2015-01-02');
    expect(mt5Preset('allTime', request.dateFrom, request.dateTo).from).toBe('2010-01-04');
    expect(() => mt5ImportRanges({ ...request, dateFrom: '2025-03-01' })).toThrow('valid date');
    expect(() => mt5Definitions({ ...request, symbols: ['UNKNOWN'] }, [])).toThrow('fetched');
  });
});

async function isolated() {
  vi.resetModules();
  const memory = new Map<string, string>();
  const storage = {
    getItem: (key: string) => memory.get(key) ?? null,
    setItem: (key: string, value: string) => { memory.set(key, value); },
  };
  vi.stubGlobal('localStorage', storage);
  const store = (await import('../../../../../app/plugins/data_source/MetaTrader/mt5ImportStore')).useMt5Import;
  return { store, memory, storage };
}

beforeEach(() => vi.unstubAllGlobals());

it('persists partial imports, restores active work paused and completes coherently', async () => {
  const { store } = await isolated();
  const definitions = mt5Definitions(request, []);
  store.getState().start(request, definitions, false);
  for (let index = 0; index < 10; index += 1) store.getState().advance();
  expect(store.getState().definitions).toHaveLength(1);
  vi.resetModules();
  const restored = (await import('../../../../../app/plugins/data_source/MetaTrader/mt5ImportStore')).useMt5Import;
  expect(restored.getState().job?.state).toBe('paused');
  restored.getState().action('resume');
  for (let index = 0; index < 20; index += 1) restored.getState().advance();
  expect(restored.getState().job?.state).toBe('completed');
  expect(restored.getState().definitions.map(row => row.symbol)).toEqual(['EURUSD_MT5', 'AAPL_MT5']);
  expect(restored.getState().ranges['mt5:AAPL_MT5']).toEqual([{ from: '2025-01-01', to: '2025-02-01' }]);
});

it('fails closed for active work, quota errors and corrupt storage', async () => {
  const { store, memory, storage } = await isolated();
  const definitions = mt5Definitions(request, []);
  expect(() => store.getState().start(request, definitions, true)).toThrow('active');
  store.getState().start(request, definitions, false);
  const prior = memory.get('sqx-mt5-import-v1');
  storage.setItem = () => { throw new Error('quota'); };
  store.getState().advance();
  expect(store.getState().job?.state).toBe('failed');
  expect(memory.get('sqx-mt5-import-v1')).toBe(prior);
  memory.set('sqx-mt5-import-v1', 'bad');
  vi.resetModules();
  const corrupt = (await import('../../../../../app/plugins/data_source/MetaTrader/mt5ImportStore')).useMt5Import;
  expect(corrupt.getState().storageError).toContain('preserved');
  expect(memory.get('sqx-mt5-import-v1')).toBe('bad');
});

it('pauses, resumes and stops without committing unfinished rows', async () => {
  const { store } = await isolated();
  const definitions = mt5Definitions(request, []);
  store.getState().start(request, definitions, false);
  store.getState().action('pause');
  expect(store.getState().job?.state).toBe('paused');
  store.getState().action('resume');
  expect(store.getState().job?.state).toBe('running');
  store.getState().action('stop');
  expect(store.getState().job?.state).toBe('cancelled');
  expect(store.getState().definitions).toEqual([]);
});
