import { beforeEach, describe, expect, it, vi } from 'vitest';
import { darwinexDefinitions, darwinexDownloadRanges, darwinexTargets } from '../../../../../app/plugins/DataSource/Darwinex/darwinex';
import { useDarwinex } from '../../../../../app/plugins/DataSource/Darwinex/darwinexStore';
import * as backend from '../../../../../app/plugins/DataSource/Darwinex/backend';

vi.mock('../../../../../app/plugins/DataSource/Darwinex/backend', () => ({ darwinexCatalog: vi.fn(), darwinexAdd: vi.fn(), darwinexDownload: vi.fn(), darwinexStatus: vi.fn(), darwinexCancel: vi.fn(), darwinexImport: vi.fn() }));
const row = { id: 'a'.repeat(32), symbol: 'EURUSD', underlying: 'EURUSD', instrument: 'EURUSD', timeframe: 'TICK' as const, broker: '-1', date_from: '', date_to: '', bars: 0, options: { metadata: { date_from: '2017-01-01' } } };
beforeEach(() => {
  vi.resetAllMocks();
  useDarwinex.setState({ definitions: [], job: null, ranges: {}, backendAvailable: false, storageError: '' });
  vi.mocked(backend.darwinexCatalog).mockResolvedValue({ available: true, reason: '', datasets: [row], symbols: [{ symbol: 'EURUSD', date_from: '2017-01-01', decimals: 5 }] });
});
describe('Darwinex provider inputs', () => {
  it('submits source identities for backend catalog validation', () => {
    expect(darwinexDefinitions(['EURUSD'], '_D', [])[0]).toMatchObject({ symbol: 'EURUSD_D', underlying: 'EURUSD', bars: 0 });
    expect(() => darwinexDefinitions(['EURUSD'], '', ['EURUSD'])).toThrow('exists');
  });
  it('calculates dates from source metadata and rejects cloned targets', () => {
    const targets = darwinexDefinitions(['EURUSD', 'GBPUSD'], '_D', []); targets[0].to = '2025-01-01'; targets[1].to = '2025-02-01';
    const request = { targets, dateFrom: '2025-01-01', dateTo: '2025-03-01', dateType: 'sinceLast' as const, overwrite: false };
    expect(darwinexDownloadRanges(request)[targets[1].id].from).toBe('2025-02-01');
    expect(() => darwinexTargets([{ ...targets[0], sourceDataId: 'clone' }])).toThrow('cloned');
    expect(() => darwinexDownloadRanges({ ...request, dateFrom: 'bad' })).toThrow('valid date');
  });
});
it('does not treat browser data or timers as acquisition evidence', async () => {
  vi.stubGlobal('localStorage', { getItem: () => JSON.stringify({ definitions: [row], job: { state: 'completed' } }), setItem: vi.fn() });
  expect(useDarwinex.getState().definitions).toEqual([]);
  await useDarwinex.getState().refresh();
  vi.mocked(backend.darwinexDownload).mockResolvedValue({ job_id: 'host-job' });
  const target = useDarwinex.getState().definitions[0];
  await useDarwinex.getState().download({ targets: [target], dateFrom: '2025-01-01', dateTo: '2025-01-03', dateType: 'custom', overwrite: false }, true, false);
  for (let i = 0; i < 100; i++) useDarwinex.getState().advance();
  expect(useDarwinex.getState().job?.state).toBe('running');
  expect(useDarwinex.getState().definitions[0].bars).toBe(0);
  vi.mocked(backend.darwinexStatus).mockResolvedValue({ state: 'succeeded', completed_chunks: 1, total_chunks: 1, rows: 2 });
  vi.mocked(backend.darwinexCatalog).mockResolvedValue({ available: true, reason: '', datasets: [{ ...row, bars: 2, date_from: '2025-01-01', date_to: '2025-01-03' }], symbols: [] });
  await useDarwinex.getState().poll();
  expect(useDarwinex.getState().job?.state).toBe('completed');
  expect(useDarwinex.getState().definitions[0].bars).toBe(2);
  expect(localStorage.setItem).not.toHaveBeenCalled();
});
it('blocks acquisition on missing or stale backend state and preserves the last snapshot', async () => {
  await expect(useDarwinex.getState().start('add', darwinexDefinitions(['AAPL'], '', []), false)).rejects.toThrow('unavailable');
  await useDarwinex.getState().refresh();
  await expect(useDarwinex.getState().start('add', darwinexDefinitions(['MSFT'], '', []), true)).rejects.toThrow('active');
  vi.mocked(backend.darwinexCatalog).mockRejectedValue(new Error('Connection lost'));
  await useDarwinex.getState().refresh();
  expect(useDarwinex.getState().definitions[0].id).toBe(row.id);
  expect(useDarwinex.getState().backendAvailable).toBe(false);
  expect(useDarwinex.getState().storageError).toBe('Connection lost');
});
it('propagates add errors and does not publish invented definitions', async () => {
  await useDarwinex.getState().refresh();
  vi.mocked(backend.darwinexAdd).mockRejectedValue(new Error('Symbol unavailable'));
  await expect(useDarwinex.getState().start('add', darwinexDefinitions(['UNKNOWN'], '', []), false)).rejects.toThrow('Symbol unavailable');
  expect(useDarwinex.getState().definitions).toHaveLength(1);
  expect(useDarwinex.getState().job?.state).toBe('failed');
});

it('does not submit the next target when cancellation races with completion', async () => {
  await useDarwinex.getState().refresh();
  vi.mocked(backend.darwinexDownload).mockResolvedValue({ job_id: 'first-job' });
  vi.mocked(backend.darwinexCancel).mockResolvedValue({ state: 'cancelled', completed_chunks: 0, total_chunks: 1, rows: 0 });
  const target = useDarwinex.getState().definitions[0];
  await useDarwinex.getState().download({ targets: [target, { ...target, id: 'b'.repeat(32) }], dateFrom: '2025-01-01', dateTo: '2025-01-03', dateType: 'custom', overwrite: false }, true, false);
  let finish!: (value: Awaited<ReturnType<typeof backend.darwinexStatus>>) => void;
  vi.mocked(backend.darwinexStatus).mockReturnValue(new Promise(resolve => { finish = resolve; }));
  const poll = useDarwinex.getState().poll();
  useDarwinex.getState().action('stop');
  finish({ state: 'succeeded', completed_chunks: 1, total_chunks: 1, rows: 2 });
  await poll;
  expect(backend.darwinexDownload).toHaveBeenCalledTimes(1);
  expect(useDarwinex.getState().job?.state).toBe('cancelled');
});
