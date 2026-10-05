import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defaultSQConfig } from '../../../../../app/plugins/DataSource/SQData/sqData';
const api = vi.hoisted(() => ({ sqCatalog: vi.fn(), sqLookup: vi.fn(), sqAdd: vi.fn() }));
vi.mock('../../../../../app/plugins/DataSource/SQData/backend', () => api);
const symbol = { ticker: 'AAPL', name: 'Apple', exchange: 'NASDAQ', timeframe: 'D', date_from: '1980-12-12', date_to: '', commodity_code: null };
async function isolated() {
  vi.resetModules();
  return (await import('../../../../../app/plugins/DataSource/SQData/sqDataStore')).useSQData;
}
beforeEach(() => {
  vi.clearAllMocks();
  vi.stubGlobal('localStorage', { getItem: vi.fn(() => null), setItem: vi.fn() });
  api.sqCatalog.mockResolvedValue({ available: true, reason: '', datasets: [], exchanges: ['NASDAQ'], credentials_configured: true });
  api.sqLookup.mockImplementation(async (_provider, config) => ({ symbols: [{ ...symbol, ticker: config.symbols }] }));
  api.sqAdd.mockResolvedValue({ id: 'actual-id' });
});
afterEach(() => vi.unstubAllGlobals());
describe('SQ backend additions', () => {
  it('uses actual catalogs and script authentication availability', async () => {
    const store = await isolated(); await store.getState().refresh();
    expect(store.getState()).toMatchObject({ backendAvailable: true, credentials: { equity: true, futures: true }, definitions: [] });
    expect(api.sqCatalog).toHaveBeenCalledWith('equity');
    expect(api.sqCatalog).toHaveBeenCalledWith('futures');
  });
  it('reports completion only after both backend definitions commit', async () => {
    const store = await isolated();
    store.getState().start('equity', defaultSQConfig(), ['AAPL', 'MSFT'], true, 'Starter', [], false);
    expect(store.getState().job).toMatchObject({ state: 'running', completed: 0, canPause: false });
    for (let i=0;i<20;i++) store.getState().advance();
    expect(store.getState().job?.completed).toBe(0);
    expect(() => store.getState().start('futures', defaultSQConfig(), ['ES'], true, 'Full', [], false)).toThrow('active');
    await vi.waitFor(() => expect(store.getState().job).toMatchObject({ state: 'completed', completed: 2, progress: 100 }));
    expect(api.sqAdd.mock.calls.map(call => call[1].ticker)).toEqual(['AAPL', 'MSFT']);
    expect(localStorage.setItem).not.toHaveBeenCalled();
  });
  it('cancels before starting another definition while accounting for an in-flight commit', async () => {
    const store = await isolated();
    let complete!: () => void;
    api.sqAdd.mockImplementationOnce(() => new Promise(resolve => { complete=()=>resolve({ id: 'committed' }); }));
    store.getState().start('equity', defaultSQConfig(), ['AAPL', 'MSFT'], true, 'Full', [], false);
    await vi.waitFor(() => expect(api.sqAdd).toHaveBeenCalledTimes(1));
    store.getState().action('stop'); complete();
    await vi.waitFor(() => expect(store.getState().job).toMatchObject({ state: 'cancelled', completed: 1 }));
    expect(api.sqAdd).toHaveBeenCalledTimes(1);
  });
  it('retains committed progress when a subsequent backend operation fails', async () => {
    const store = await isolated(); api.sqAdd.mockResolvedValueOnce({ id: 'committed' }).mockRejectedValueOnce(new Error('Storage unavailable'));
    store.getState().start('equity', defaultSQConfig(), ['AAPL', 'MSFT'], true, 'Full', [], false);
    await vi.waitFor(() => expect(store.getState().job).toMatchObject({ state: 'failed', completed: 1, error: 'Storage unavailable' }));
  });
  it('requires consent, unique names and supported timestamps before invoking a source', async () => {
    const store = await isolated();
    expect(() => store.getState().start('equity', defaultSQConfig(), ['AAPL'], false, 'Full', [], false)).toThrow('accept');
    expect(() => store.getState().start('equity', defaultSQConfig(), ['AAPL'], true, 'Full', ['AAPL'], false)).toThrow('exists');
    expect(() => store.getState().start('equity', { ...defaultSQConfig(), timezoneType: 0 }, ['AAPL'], true, 'Full', [], false)).toThrow('UTC');
    expect(api.sqAdd).not.toHaveBeenCalled();
  });
  it('reports unavailable providers without fabricating definitions', async () => {
    const store = await isolated(); api.sqCatalog.mockRejectedValue(new Error('Host offline')); await store.getState().refresh();
    expect(store.getState()).toMatchObject({ backendAvailable: false, definitions: [], storageError: 'Host offline Host offline' });
  });
});
