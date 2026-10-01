import { beforeEach, describe, expect, it, vi } from 'vitest';
import { customFormat, emptyFileRecord, massSymbol, previewRows } from '../../../../../app/plugins/DataSource/FileImport/fileImport';
import { newInstrument } from '../../../../../app/plugins/DataSource/FileImport/presentation';
import { useFileImports } from '../../../../../app/plugins/DataSource/FileImport/fileImportStore';
import * as backend from '../../../../../app/plugins/DataSource/FileImport/backend';

vi.mock('../../../../../app/plugins/DataSource/FileImport/backend', async importOriginal => {
  const real = await importOriginal<typeof backend>();
  return { ...real, fileCatalog: vi.fn(), fileStart: vi.fn(), fileStatus: vi.fn(), fileCancel: vi.fn(), fileSaveFormat: vi.fn(), fileDeleteFormat: vi.fn(), filePublishGroup: vi.fn() };
});
const catalog = { available: true, reason: '', datasets: [], formats: [], custom_formats: [] };
beforeEach(() => {
  vi.resetAllMocks();
  useFileImports.setState({ records: [], job: null, backendAvailable: false, storageError: '', formats: [], predefinedFormats: [] });
  vi.mocked(backend.fileCatalog).mockResolvedValue(catalog);
});
function task() {
  const base = emptyFileRecord('EURUSD', newInstrument(), 'start');
  return { filename: 'input.csv', ignored: 0, record: { ...base, timestamps: [], unknownBars: 0 },
    request: backend.wireRequest('2024.01.02,1,2,0,1,4', { ...customFormat(), columns: ['Date', 'Open', 'High', 'Low', 'Close', 'Volume'] }, 'EURUSD', 'EURUSD', 'D1', false) };
}
describe('file presentation', () => {
  it('previews raw cells without frontend numerical interpretation', () => {
    expect(previewRows('header\n2024.01.02;1,25;2', { ...customFormat(), separator: ';', skipRows: 1 })).toEqual([['2024.01.02', '1,25', '2']]);
  });
  it('protects other sources when choosing a mass-import name', () => {
    expect(() => massSymbol('EURUSD', '', [{ symbol: 'EURUSD', source: 'Dukascopy' }], 'overwrite')).toThrow('Dukascopy');
    expect(massSymbol('EURUSD', '', [{ symbol: 'EURUSD', source: 'Dukascopy' }], 'create')).toBe('EURUSD2');
  });
});
it('uses backend jobs and only committed inventory for completion', async () => {
  await useFileImports.getState().refresh();
  vi.mocked(backend.fileStart).mockResolvedValue({ job_id: 'import-job' });
  await useFileImports.getState().start([task()], 'UTC', '', 0, false);
  expect(useFileImports.getState().records).toEqual([]);
  expect(useFileImports.getState().job?.state).toBe('running');
  vi.mocked(backend.fileStatus).mockResolvedValue({ job_id: 'import-job', state: 'succeeded', rows: 1, ignored_rows: 0, published_partitions: 1, total_partitions: 1 });
  vi.mocked(backend.fileCatalog).mockResolvedValue({ ...catalog, datasets: [{ id: 'real-id', symbol: 'EURUSD', underlying: 'EURUSD', instrument: 'EURUSD', timeframe: 'D1', timezone: 'UTC', date_from: '2024-01-02', date_to: '2024-01-02', bars: 1 }] });
  await useFileImports.getState().poll();
  expect(useFileImports.getState().job?.state).toBe('completed');
  expect(useFileImports.getState().records[0]).toMatchObject({ id: 'real-id', bars: 1 });
});
it('fails closed when custody is unavailable and does not fabricate timezone conversion', async () => {
  await expect(useFileImports.getState().start([task()], 'UTC', '', 0, false)).rejects.toThrow('unavailable');
  await useFileImports.getState().refresh();
  await expect(useFileImports.getState().start([task()], 'EETUS', '', 0, false)).rejects.toThrow('UTC');
  expect(backend.fileStart).not.toHaveBeenCalled();
});
it('persists custom formats through backend custody', async () => {
  vi.mocked(backend.fileSaveFormat).mockResolvedValue({ success: true });
  const format = { ...customFormat(), name: 'Saved', columns: ['Date', 'Close'] as ('Date' | 'Close')[] };
  await useFileImports.getState().saveFormat(format);
  expect(backend.fileSaveFormat).toHaveBeenCalledWith(format, false);
  vi.mocked(backend.fileDeleteFormat).mockRejectedValue(new Error('Custody unavailable'));
  await expect(useFileImports.getState().deleteFormat('Saved')).rejects.toThrow('Custody unavailable');
});
it('publishes a folder group only after its data is committed', async () => {
  await useFileImports.getState().refresh();
  vi.mocked(backend.fileStart).mockResolvedValue({ job_id: 'folder-job' });
  await useFileImports.getState().start([task()], 'UTC', 'Folder', 0, false);
  expect(backend.filePublishGroup).not.toHaveBeenCalled();
  vi.mocked(backend.fileStatus).mockResolvedValue({ job_id: 'folder-job', state: 'succeeded', rows: 1, ignored_rows: 0, published_partitions: 1, total_partitions: 1 });
  vi.mocked(backend.filePublishGroup).mockRejectedValue(new Error('Catalog revision changed'));
  await useFileImports.getState().poll();
  expect(backend.filePublishGroup).toHaveBeenCalledWith('Folder', ['EURUSD']);
  expect(useFileImports.getState().job).toMatchObject({ state: 'failed', completed: 1, error: 'Catalog revision changed' });
});
