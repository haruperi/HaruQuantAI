import { beforeEach, describe, expect, it, vi } from 'vitest';
import { discoverTD, validateTD } from '../../../../../app/plugins/DataSource/TickDownloader/tickDownloader';
import { useTickDownloader } from '../../../../../app/plugins/DataSource/TickDownloader/tickDownloaderStore';
import * as backend from '../../../../../app/plugins/DataSource/TickDownloader/backend';

vi.mock('../../../../../app/plugins/DataSource/TickDownloader/backend', () => ({ tdCatalog: vi.fn(), tdInspect: vi.fn(), tdImport: vi.fn(), tdStatus: vi.fn(), tdCancel: vi.fn(), encodeBI5: vi.fn() }));
beforeEach(() => {
  vi.resetAllMocks();
  useTickDownloader.setState({ definitions: [], job: null, backendAvailable: false, storageError: '' });
  vi.mocked(backend.tdCatalog).mockResolvedValue({ available: true, reason: '', datasets: [] });
});
describe('TickDownloader discovery and validation', () => {
  it('prefers installation tickdata folders and deduplicates file-backed symbols', () => {
    expect(discoverTD(['TD/tickdata/EURUSD/2020/a.bin', 'TD/tickdata/EURUSD/2020/b.bin', 'TD/tickdata/GBPUSD/a.bin', 'TD/bin/app.exe']).symbols).toEqual(['EURUSD', 'GBPUSD']);
  });
  it('supports a directly selected data folder and ignores root files', () => {
    expect(discoverTD(['tickdata/EURUSD/data.bin', 'tickdata/readme.txt']).symbols).toEqual(['EURUSD']);
    expect(discoverTD(['empty/readme.txt']).symbols).toEqual([]);
  });
  it('bounds discovery and rejects invalid relative paths', () => {
    expect(() => discoverTD([])).toThrow();
    expect(() => discoverTD(['TD/../secret'])).toThrow();
    expect(() => discoverTD(['TD/a/x', 'Other/b/x'])).toThrow();
    expect(() => discoverTD(Array(20001).fill('TD/a/x'))).toThrow('20,000');
  });
  it('rejects missing selection, unknown symbols and duplicate names', () => {
    const request = { folder: 'TD', symbols: ['EURUSD'], postfix: '' };
    expect(() => validateTD(request, ['EURUSD'], ['EURUSD'])).toThrow('postfix');
    expect(() => validateTD({ ...request, symbols: [] }, ['EURUSD'], [])).toThrow('at least one');
    expect(() => validateTD(request, ['GBPUSD'], [])).toThrow('chosen folder');
    expect(() => validateTD({ ...request, postfix: '_TD' }, ['EURUSD'], ['EURUSD'])).not.toThrow();
  });
});

it('uploads actual selected files and waits for stored rows before completion', async () => {
  await useTickDownloader.getState().refresh();
  const path = 'TD/EURUSD/2024/00/01/00h_ticks.bi5';
  const file = { webkitRelativePath: path, size: 24 } as File;
  vi.mocked(backend.tdInspect).mockResolvedValue({ files: [{ path, symbol: 'EURUSD', hour: '2024-01-01T00:00:00Z', decimals: 5 }] });
  vi.mocked(backend.encodeBI5).mockResolvedValue('actual-uploaded-content');
  vi.mocked(backend.tdImport).mockResolvedValue({ job_id: 'backend-job' });
  await useTickDownloader.getState().start({ folder: 'TD', symbols: ['EURUSD'], postfix: '_TD' }, ['EURUSD'], [], false, [file]);
  expect(backend.encodeBI5).toHaveBeenCalledWith(file);
  expect(backend.tdImport).toHaveBeenCalledWith('EURUSD', '_TD', 5, [{ hour: '2024-01-01T00:00:00Z', content_base64: 'actual-uploaded-content' }]);
  for (let i = 0; i < 100; i++) useTickDownloader.getState().advance();
  expect(useTickDownloader.getState().job?.state).toBe('running');
  expect(useTickDownloader.getState().definitions).toEqual([]);
  vi.mocked(backend.tdStatus).mockResolvedValue({ state: 'succeeded', rows: 2, completed_files: 1, total_files: 1 });
  vi.mocked(backend.tdCatalog).mockResolvedValue({ available: true, reason: '', datasets: [{ id: 'a'.repeat(32), symbol: 'EURUSD_TD', underlying: 'EURUSD', instrument: 'EURUSD', timeframe: 'TICK', date_from: '2024-01-01', date_to: '2024-01-01', bars: 2 }] });
  await useTickDownloader.getState().poll();
  expect(useTickDownloader.getState().job?.state).toBe('completed');
  expect(useTickDownloader.getState().definitions[0].bars).toBe(2);
});

it('refuses to claim an import from filenames without file contents', async () => {
  await useTickDownloader.getState().refresh();
  await expect(useTickDownloader.getState().start({ folder: 'TD', symbols: ['EURUSD'], postfix: '' }, ['EURUSD'])).rejects.toThrow('actual BI5');
  expect(backend.tdImport).not.toHaveBeenCalled();
  expect(useTickDownloader.getState().job).toBeNull();
});
