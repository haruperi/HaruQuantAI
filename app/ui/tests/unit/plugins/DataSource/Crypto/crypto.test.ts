import { beforeEach, describe, expect, it, vi } from 'vitest';
import { cryptoDefinitions, cryptoDownloadRanges, cryptoTargets } from '../../../../../app/plugins/DataSource/Crypto/crypto';
import { useCrypto } from '../../../../../app/plugins/DataSource/Crypto/cryptoStore';
import * as backend from '../../../../../app/plugins/DataSource/Crypto/backend';

vi.mock('../../../../../app/plugins/DataSource/Crypto/backend', () => ({ exchangeId: (name: string) => name === 'Coinbase Pro' ? 'Coinbase' : name, cryptoCatalog: vi.fn(), cryptoAdd: vi.fn(), cryptoDownload: vi.fn(), cryptoStatus: vi.fn(), cryptoCancel: vi.fn() }));
const row = { id: 'a'.repeat(32), symbol: 'BTCUSD', underlying: 'BTC-USD', instrument: 'BTCUSD', timeframe: 'D1', date_from: '', date_to: '', bars: 0, options: { parameters: { exchange: 'Coinbase Pro' }, metadata: { date_from: 1577836800000 } } };
beforeEach(() => {
  vi.resetAllMocks();
  useCrypto.setState({ definitions: [], job: null, ranges: {}, backendAvailable: false, storageError: '' });
  vi.mocked(backend.cryptoCatalog).mockResolvedValue({ available: true, reason: '', datasets: [row], exchanges: [{ name: 'Coinbase Pro', timeframes: ['M1', 'D1'] }] });
});
describe('Crypto provider inputs', () => {
  it('keeps native exchange symbols as inputs for backend validation', () => {
    expect(cryptoDefinitions('Coinbase', ['BTC-USD'], 'D1', '_C', [])[0]).toMatchObject({ underlying: 'BTC-USD', exchange: 'Coinbase', bars: 0 });
    expect(() => cryptoDefinitions('Coinbase', [], 'D1', '', [])).toThrow('No symbols');
    expect(() => cryptoDefinitions('Coinbase', ['BTC-USD'], 'D1', '', ['BTC-USD'])).toThrow('exists');
  });
  it('calculates dates from source metadata and rejects cloned targets', () => {
    const targets = cryptoDefinitions('Coinbase', ['BTC-USD', 'ETH-USD'], 'D1', '_C', []); targets[0].to = '2025-01-01'; targets[1].to = '2025-02-01';
    const request = { targets, dateFrom: '2025-01-01', dateTo: '2025-03-01', dateType: 'sinceLast' as const, overwrite: false };
    expect(cryptoDownloadRanges(request)[targets[1].id].from).toBe('2025-02-01');
    expect(() => cryptoTargets([{ ...targets[0], sourceDataId: 'clone' }])).toThrow('cloned');
    expect(() => cryptoDownloadRanges({ ...request, dateFrom: 'bad' })).toThrow('valid date');
  });
});
it('does not treat browser data or timers as acquisition evidence', async () => {
  vi.stubGlobal('localStorage', { getItem: () => JSON.stringify({ definitions: [row], job: { state: 'completed' } }), setItem: vi.fn() });
  expect(useCrypto.getState().definitions).toEqual([]);
  await useCrypto.getState().refresh();
  vi.mocked(backend.cryptoDownload).mockResolvedValue({ job_id: 'host-job' });
  const target = useCrypto.getState().definitions[0];
  await useCrypto.getState().startDownload({ targets: [target], dateFrom: '2025-01-01', dateTo: '2025-01-03', dateType: 'custom', overwrite: false }, false);
  for (let i = 0; i < 100; i++) useCrypto.getState().advance();
  expect(useCrypto.getState().job?.state).toBe('running');
  expect(useCrypto.getState().definitions[0].bars).toBe(0);
  vi.mocked(backend.cryptoStatus).mockResolvedValue({ job_id: 'host-job', state: 'succeeded', progress: 1, published_partitions: 1, rows: 2 });
  vi.mocked(backend.cryptoCatalog).mockResolvedValue({ available: true, reason: '', datasets: [{ ...row, bars: 2, date_from: '2025-01-01', date_to: '2025-01-03' }], exchanges: [{ name: 'Coinbase Pro', timeframes: ['M1', 'D1'] }] });
  await useCrypto.getState().poll();
  expect(useCrypto.getState().job?.state).toBe('completed');
  expect(useCrypto.getState().definitions[0].bars).toBe(2);
  expect(localStorage.setItem).not.toHaveBeenCalled();
});
it('blocks acquisition on missing or stale backend state and preserves the last snapshot', async () => {
  await expect(useCrypto.getState().startAdd(cryptoDefinitions('Coinbase', ['AAPL'], 'D1', '', []), false)).rejects.toThrow('unavailable');
  await useCrypto.getState().refresh();
  await expect(useCrypto.getState().startAdd(cryptoDefinitions('Coinbase', ['MSFT'], 'D1', '', []), true)).rejects.toThrow('active');
  vi.mocked(backend.cryptoCatalog).mockRejectedValue(new Error('Connection lost'));
  await useCrypto.getState().refresh();
  expect(useCrypto.getState().definitions[0].id).toBe(row.id);
  expect(useCrypto.getState().backendAvailable).toBe(false);
  expect(useCrypto.getState().storageError).toBe('Connection lost');
});
it('propagates add errors and does not publish invented definitions', async () => {
  await useCrypto.getState().refresh();
  vi.mocked(backend.cryptoAdd).mockRejectedValue(new Error('Symbol unavailable'));
  await expect(useCrypto.getState().startAdd(cryptoDefinitions('Coinbase', ['UNKNOWN'], 'D1', '', []), false)).rejects.toThrow('Symbol unavailable');
  expect(useCrypto.getState().definitions).toHaveLength(1);
  expect(useCrypto.getState().job?.state).toBe('failed');
});

it('does not submit the next target when cancellation races with completion', async () => {
  await useCrypto.getState().refresh();
  vi.mocked(backend.cryptoDownload).mockResolvedValue({ job_id: 'first-job' });
  vi.mocked(backend.cryptoCancel).mockResolvedValue({ job_id: 'first-job', state: 'cancelled', progress: 0, published_partitions: 0, rows: 0 });
  const target = useCrypto.getState().definitions[0];
  await useCrypto.getState().startDownload({ targets: [target, { ...target, id: 'b'.repeat(32) }], dateFrom: '2025-01-01', dateTo: '2025-01-03', dateType: 'custom', overwrite: false }, false);
  let finish!: (value: Awaited<ReturnType<typeof backend.cryptoStatus>>) => void;
  vi.mocked(backend.cryptoStatus).mockReturnValue(new Promise(resolve => { finish = resolve; }));
  const poll = useCrypto.getState().poll();
  useCrypto.getState().action('stop');
  finish({ job_id: 'first-job', state: 'succeeded', progress: 1, published_partitions: 1, rows: 2 });
  await poll;
  expect(backend.cryptoDownload).toHaveBeenCalledTimes(1);
  expect(useCrypto.getState().job?.state).toBe('cancelled');
});
