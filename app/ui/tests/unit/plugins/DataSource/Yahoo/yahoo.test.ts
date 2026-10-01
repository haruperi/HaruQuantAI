import { beforeEach, describe, expect, it, vi } from 'vitest';
import { parseYahooSymbols, yahooDefinitions, yahooDownloadRanges, yahooTargets } from '../../../../../app/plugins/DataSource/Yahoo/yahoo';
import { useYahoo } from '../../../../../app/plugins/DataSource/Yahoo/yahooStore';
import * as backend from '../../../../../app/plugins/DataSource/Yahoo/backend';

vi.mock('../../../../../app/plugins/DataSource/Yahoo/backend', () => ({ yahooCatalog: vi.fn(), yahooAdd: vi.fn(), yahooDownload: vi.fn(), yahooStatus: vi.fn(), yahooCancel: vi.fn() }));
const row = { id: 'a'.repeat(32), symbol: 'AAPL', underlying: 'AAPL', instrument: 'AAPL', timeframe: 'D1', date_from: '', date_to: '', bars: 0, options: { metadata: { shortName: 'Apple', exchangeName: 'NASDAQ', instrumentType: 'EQUITY', firstTradeDate: 345427200 } } };
beforeEach(() => {
  vi.resetAllMocks();
  useYahoo.setState({ definitions: [], job: null, ranges: {}, backendAvailable: false, storageError: '' });
  vi.mocked(backend.yahooCatalog).mockResolvedValue({ available: true, reason: '', datasets: [row] });
});
describe('Yahoo provider inputs', () => {
  it('accepts arbitrary tickers for backend validation without inventing metadata', () => {
    expect(parseYahooSymbols(' AAPL,msft;\nTSLA ')).toEqual(['AAPL', 'MSFT', 'TSLA']);
    expect(yahooDefinitions('NEW_TICKER', '_Y', [])[0]).toMatchObject({ symbol: 'NEW_TICKER_Y', underlying: 'NEW_TICKER', exchange: '', category: 'Unknown' });
    expect(() => parseYahooSymbols('AAPL,aapl')).toThrow('duplicate');
    expect(() => yahooDefinitions('AAPL', '', ['AAPL'])).toThrow('exists');
  });
  it('calculates dates from source metadata and rejects cloned targets', () => {
    const targets = yahooDefinitions('AAPL;MSFT', '_Y', []); targets[0].to = '2025-01-01'; targets[1].to = '2025-02-01';
    const request = { targets, dateFrom: '2025-01-01', dateTo: '2025-03-01', dateType: 'sinceLast' as const, overwrite: false };
    expect(yahooDownloadRanges(request)[targets[1].id].from).toBe('2025-02-01');
    expect(() => yahooTargets([{ ...targets[0], sourceDataId: 'clone' }])).toThrow('cloned');
    expect(() => yahooDownloadRanges({ ...request, dateFrom: 'bad' })).toThrow('valid date');
  });
});
it('does not treat browser data or timers as acquisition evidence', async () => {
  vi.stubGlobal('localStorage', { getItem: () => JSON.stringify({ definitions: [row], job: { state: 'completed' } }), setItem: vi.fn() });
  expect(useYahoo.getState().definitions).toEqual([]);
  await useYahoo.getState().refresh();
  vi.mocked(backend.yahooDownload).mockResolvedValue({ job_id: 'host-job' });
  const target = useYahoo.getState().definitions[0];
  await useYahoo.getState().startDownload({ targets: [target], dateFrom: '2025-01-01', dateTo: '2025-01-03', dateType: 'custom', overwrite: false }, false);
  for (let i = 0; i < 100; i++) useYahoo.getState().advance();
  expect(useYahoo.getState().job?.state).toBe('running');
  expect(useYahoo.getState().definitions[0].bars).toBe(0);
  vi.mocked(backend.yahooStatus).mockResolvedValue({ job_id: 'host-job', state: 'succeeded', completed_chunks: 1, total_chunks: 1, published_partitions: 1, rows: 2 });
  vi.mocked(backend.yahooCatalog).mockResolvedValue({ available: true, reason: '', datasets: [{ ...row, bars: 2, date_from: '2025-01-01', date_to: '2025-01-03' }] });
  await useYahoo.getState().poll();
  expect(useYahoo.getState().job?.state).toBe('completed');
  expect(useYahoo.getState().definitions[0].bars).toBe(2);
  expect(localStorage.setItem).not.toHaveBeenCalled();
});
it('blocks acquisition on missing or stale backend state and preserves the last snapshot', async () => {
  await expect(useYahoo.getState().startAdd(yahooDefinitions('AAPL', '', []), false)).rejects.toThrow('unavailable');
  await useYahoo.getState().refresh();
  await expect(useYahoo.getState().startAdd(yahooDefinitions('MSFT', '', []), true)).rejects.toThrow('active');
  vi.mocked(backend.yahooCatalog).mockRejectedValue(new Error('Connection lost'));
  await useYahoo.getState().refresh();
  expect(useYahoo.getState().definitions[0].id).toBe(row.id);
  expect(useYahoo.getState().backendAvailable).toBe(false);
  expect(useYahoo.getState().storageError).toBe('Connection lost');
});
it('propagates add errors and does not publish invented definitions', async () => {
  await useYahoo.getState().refresh();
  vi.mocked(backend.yahooAdd).mockRejectedValue(new Error('Symbol unavailable'));
  await expect(useYahoo.getState().startAdd(yahooDefinitions('UNKNOWN', '', []), false)).rejects.toThrow('Symbol unavailable');
  expect(useYahoo.getState().definitions).toHaveLength(1);
  expect(useYahoo.getState().job?.state).toBe('failed');
});

it('does not submit the next target when cancellation races with completion', async () => {
  await useYahoo.getState().refresh();
  vi.mocked(backend.yahooDownload).mockResolvedValue({ job_id: 'first-job' });
  vi.mocked(backend.yahooCancel).mockResolvedValue({ job_id: 'first-job', state: 'cancelled', completed_chunks: 0, total_chunks: 1, published_partitions: 0, rows: 0 });
  const target = useYahoo.getState().definitions[0];
  await useYahoo.getState().startDownload({ targets: [target, { ...target, id: 'b'.repeat(32) }], dateFrom: '2025-01-01', dateTo: '2025-01-03', dateType: 'custom', overwrite: false }, false);
  let finish!: (value: Awaited<ReturnType<typeof backend.yahooStatus>>) => void;
  vi.mocked(backend.yahooStatus).mockReturnValue(new Promise(resolve => { finish = resolve; }));
  const poll = useYahoo.getState().poll();
  useYahoo.getState().action('stop');
  finish({ job_id: 'first-job', state: 'succeeded', completed_chunks: 1, total_chunks: 1, published_partitions: 1, rows: 2 });
  await poll;
  expect(backend.yahooDownload).toHaveBeenCalledTimes(1);
  expect(useYahoo.getState().job?.state).toBe('cancelled');
});
