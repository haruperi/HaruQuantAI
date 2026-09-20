import { describe, expect, it, vi } from 'vitest';
import { parseYahooSymbols, yahooDefinitions, yahooDownloadRanges, yahooTargets } from './yahoo';

describe('Yahoo provider rules', () => {
  it('parses supported separators, trims input and creates D1 metadata', () => {
    expect(parseYahooSymbols(' AAPL,MSFT;\nTSLA ')).toEqual(['AAPL', 'MSFT', 'TSLA']);
    expect(yahooDefinitions('aapl; EURUSD=X', '_Y', [])[0]).toMatchObject({ id: 'yahoo:AAPL_Y', symbol: 'AAPL_Y', underlying: 'AAPL', name: 'Apple Inc.', exchange: 'NASDAQ', source: 'Yahoo', timeframe: 'D1' });
    expect(() => parseYahooSymbols('AAPL,aapl')).toThrow('duplicate');
    expect(() => yahooDefinitions('UNKNOWN', '', [])).toThrow("not found");
    expect(() => yahooDefinitions('AAPL', '', ['AAPL'])).toThrow('exists');
  });

  it('isolates Yahoo targets and calculates per-record ranges', () => {
    const targets = yahooDefinitions('AAPL;MSFT', '_Y', []); targets[0].to = '2025-01-01'; targets[1].to = '2025-02-01';
    const request = { targets, dateFrom: '2025-01-01', dateTo: '2025-03-01', dateType: 'sinceLast' as const, overwrite: false };
    expect(yahooDownloadRanges(request)[targets[1].id].from).toBe('2025-02-01');
    expect(() => yahooTargets([{ ...targets[0], sourceDataId: 'clone' }])).toThrow('cloned');
    expect(() => yahooDownloadRanges({ ...request, dateFrom: 'bad' })).toThrow('valid date');
  });
});

async function isolated() {
  vi.resetModules(); const memory = new Map<string,string>(); const storage = { getItem: (key:string) => memory.get(key) ?? null, setItem: (key:string,value:string) => { memory.set(key,value); } }; vi.stubGlobal('localStorage', storage);
  const store = (await import('./yahooStore')).useYahoo; return { store, memory, storage };
}

it('persists add/download jobs, restores paused and merges coverage', async () => {
  const { store } = await isolated(); const definitions = yahooDefinitions('AAPL;MSFT', '_Y', []);
  store.getState().startAdd(definitions, false); for (let i=0;i<10;i++) store.getState().advance(); expect(store.getState().definitions).toHaveLength(1);
  vi.resetModules(); const restored = (await import('./yahooStore')).useYahoo; expect(restored.getState().job?.state).toBe('paused'); restored.getState().action('resume'); for (let i=0;i<10;i++) restored.getState().advance(); expect(restored.getState().definitions).toHaveLength(2);
  const target = restored.getState().definitions[0], request = { targets: [target], dateFrom: '2025-01-01', dateTo: '2025-01-03', dateType: 'custom' as const, overwrite: false };
  restored.getState().startDownload(request, false); for (let i=0;i<20;i++) restored.getState().advance(); expect(restored.getState().ranges[target.id]).toEqual([{ from: '2025-01-01', to: '2025-01-03' }]);
  restored.getState().startDownload(request, false); for (let i=0;i<20;i++) restored.getState().advance(); expect(restored.getState().ranges[target.id]).toHaveLength(1);
});

it('fails closed for active work, quota errors and corrupt storage', async () => {
  const { store, memory, storage } = await isolated(); const definition = yahooDefinitions('AAPL', '_Y', []);
  expect(() => store.getState().startAdd(definition, true)).toThrow('active'); store.getState().startAdd(definition, false); const prior = memory.get('sqx-yahoo-data-v1'); storage.setItem = () => { throw new Error('quota'); }; store.getState().advance(); expect(store.getState().job?.state).toBe('failed'); expect(memory.get('sqx-yahoo-data-v1')).toBe(prior);
  memory.set('sqx-yahoo-data-v1', 'bad'); vi.resetModules(); const corrupt = (await import('./yahooStore')).useYahoo; expect(corrupt.getState().storageError).toContain('preserved'); expect(memory.get('sqx-yahoo-data-v1')).toBe('bad');
});
