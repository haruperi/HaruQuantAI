import { describe, expect, it, vi } from 'vitest';
import { defaultSQConfig, lookupSQ, planSQAdd } from './sqData';
describe('SQ catalogue rules', () => {
  it('combines ticker/name tokens, exchange and exact filters', () => {
    const config = { ...defaultSQConfig(), symbols: 'aapl;Microsoft\nAmazon' };
    expect(lookupSQ('equity', config).map(row => row.ticker)).toEqual(['AAPL', 'MSFT', 'AMZN']);
    expect(lookupSQ('equity', { ...config, exchange: 'NYSE' })).toEqual([]);
    expect(lookupSQ('equity', { ...config, symbols: 'AA', exact: true })).toEqual([]);
    expect(() => lookupSQ('equity', { ...config, searchInName: false, searchInTicker: false })).toThrow('Enable');
  });
  it('filters dated futures and validates entitlement and duplicate names', () => {
    const config = { ...defaultSQConfig(), symbols: 'ES', searchInName: false };
    expect(lookupSQ('futures', config).map(row => row.ticker)).toEqual(['ES']);
    expect(lookupSQ('futures', { ...config, onlyContFutures: false }).map(row => row.ticker)).toEqual(['ES', 'ESZ26']);
    expect(() => planSQAdd('futures', config, ['ES'], true, 'Full', ['ES'])).toThrow('exists');
    expect(() => planSQAdd('equity', defaultSQConfig(), ['AMZN'], true, 'Starter', [])).toThrow('subscription');
    expect(() => planSQAdd('equity', defaultSQConfig(), ['AAPL'], false, 'Full', [])).toThrow('agree');
  });
  it('adds empty definitions with configured bar and timezone metadata', () => {
    const row = planSQAdd('equity', { ...defaultSQConfig(), postfix: '_test', timezoneType: 0, timezoneShift: -2 }, ['AAPL'], true, 'Full', [])[0];
    expect(row).toMatchObject({ symbol: 'AAPL_test', bars: 0, from: '', to: '', timezone: 'Exchange -2h', barType: 'end', availableTimeframes: ['M1', 'D1'] });
    expect(() => planSQAdd('equity', { ...defaultSQConfig(), timezoneShift: 24 }, ['AAPL'], true, 'Full', [])).toThrow('integer');
  });
});
async function isolated() {
  vi.resetModules(); const memory = new Map<string, string>();
  const storage = { getItem: (key: string) => memory.get(key) ?? null, setItem: (key: string, value: string) => { memory.set(key, value); } };
  vi.stubGlobal('localStorage', storage);
  const store = (await import('./sqDataStore')).useSQData;
  return { store, memory, storage };
}
describe('SQ add persistence', () => {
  it('commits atomically, pauses, resumes after reload, and completes without duplicate rows', async () => {
    const { store } = await isolated();
    store.getState().start('equity', defaultSQConfig(), ['AAPL', 'MSFT'], true, 'Full', [], false);
    expect(() => store.getState().start('futures', defaultSQConfig(), ['ES'], true, 'Full', [], false)).toThrow('active');
    for (let i = 0; i < 10; i++) store.getState().advance();
    expect(store.getState().definitions.map(row => row.symbol)).toEqual(['AAPL']);
    vi.resetModules(); const restored = (await import('./sqDataStore')).useSQData;
    expect(restored.getState().job?.state).toBe('paused'); restored.getState().advance(); expect(restored.getState().job?.progress).toBe(50);
    restored.getState().action('resume'); for (let i = 0; i < 10; i++) restored.getState().advance();
    expect(restored.getState().definitions.map(row => row.symbol)).toEqual(['AAPL', 'MSFT']); expect(restored.getState().job?.state).toBe('completed');
  });
  it('stops unfinished additions and preserves storage on write failure or corruption', async () => {
    const { store, memory, storage } = await isolated();
    store.getState().start('futures', defaultSQConfig(), ['ES', '6E'], true, 'Full', [], false);
    for (let i = 0; i < 10; i++) store.getState().advance(); store.getState().action('stop'); store.getState().advance();
    expect(store.getState().definitions.map(row => row.symbol)).toEqual(['ES']);
    storage.setItem = () => { throw new Error('Quota'); };
    expect(() => store.getState().start('equity', defaultSQConfig(), ['AAPL'], true, 'Full', [], false)).toThrow('Unable to save');
    memory.set('sqx-sq-data-v1', '{bad'); vi.resetModules(); const restored = (await import('./sqDataStore')).useSQData;
    expect(restored.getState().storageError).toContain('preserved'); expect(memory.get('sqx-sq-data-v1')).toBe('{bad');
  });
  it('normalizes legacy product labels before validating persisted data', async () => {
    const { store, memory } = await isolated();
    store.getState().start('futures', defaultSQConfig(), ['ES'], true, 'Full', [], false);
    for (let index = 0; index < 20; index++) store.getState().advance();
    const current = memory.get('sqx-sq-data-v1');
    expect(current).toBeDefined();
    const legacy = JSON.parse(current!);
    legacy.definitions[0].source = 'SQ Futures';
    legacy.job.definitions[0].source = 'SQ Futures';
    memory.set('sqx-sq-data-v1', JSON.stringify(legacy));
    vi.resetModules();
    const restored = (await import('./sqDataStore')).useSQData;
    expect(restored.getState().storageError).toBe('');
    expect(restored.getState().definitions[0]?.source).toBe('Futures');
  });
});
it('reserves SQ names across providers and reports mid-job persistence failure', async () => {
  const { store, storage, memory } = await isolated();
  store.getState().start('equity', defaultSQConfig(), ['AAPL'], true, 'Full', [], false);
  const { reservedSQDefinitions } = await import('./sqDataStore');
  expect(reservedSQDefinitions().map(row => row.symbol)).toEqual(['AAPL']);
  const previous = memory.get('sqx-sq-data-v1'); storage.setItem = () => { throw new Error('Quota'); };
  store.getState().advance();
  expect(store.getState().job).toMatchObject({ state: 'failed', completed: 0 });
  expect(store.getState().definitions).toEqual([]); expect(memory.get('sqx-sq-data-v1')).toBe(previous);
  expect(() => store.getState().start('equity', defaultSQConfig(), ['MSFT'], true, 'Full', [], true)).toThrow('active');
});
