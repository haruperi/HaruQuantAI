import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createDomainClient } from '../../../../../shell/transport';
import {
  clearExternalIndicators,
  controlExternalImportJob,
  deleteExternalIndicators,
  deleteExternalImportFormat,
  editExternalIndicator,
  exportExternalIndicatorValues,
  fetchExternalImportInfo,
  fetchExternalImportJob,
  fetchExternalIndicators,
  fetchExternalReview,
  importExternalIndicatorData,
  loadExternalDefinitions,
  previewExternalIndicatorImport,
  recognizeExternalIndicator,
  saveExternalDefinitions,
  saveExternalImportFormat,
  saveExternalIndicator,
  setExternalIndicatorsApiClient,
  toExternalImportFormat,
  toExternalIndicatorDefinition,
  updateCotIndicators,
  type RemoteIndicatorRecord,
} from '../../../../../workspaces/data_manager/plugins/Indicators/externalIndicatorsApiClient';
import { useExternalIndicators } from '../../../../../workspaces/data_manager/plugins/Indicators/externalIndicatorsStore';

const mockRecord: RemoteIndicatorRecord = {
  id: '1',
  name: 'Sentiment',
  data_type: 'custom',
  timeframe: 'D1',
  system: false,
  values: [{ name: 'Score', mt4: '0', mt5: '0', el: '0' }],
  total_records: 10,
  date_from: '2026-01-01',
  date_to: '2026-01-10',
  total_days: 10,
};

const response = (data: unknown) => new Response(JSON.stringify({ status: 'success', data }));

const storageMap = new Map<string, string>();
const mockStorage = {
  getItem: (k: string) => storageMap.get(k) ?? null,
  setItem: (k: string, v: string) => {
    storageMap.set(k, String(v));
  },
  removeItem: (k: string) => {
    storageMap.delete(k);
  },
  clear: () => storageMap.clear(),
  length: 0,
  key: () => null,
};
Object.defineProperty(globalThis, 'localStorage', { value: mockStorage, writable: true, configurable: true });

function setup() {
  const fetchFn = vi.fn();
  setExternalIndicatorsApiClient(createDomainClient('/data', { fetchFn, baseUrl: '/api/v1' }));
  return fetchFn;
}

beforeEach(() => {
  storageMap.clear();
  useExternalIndicators.setState({ definitions: [], formats: [], job: null, storageError: '' });
});

describe('externalIndicatorsApiClient', () => {
  it('fetches external indicators and maps definition properties', async () => {
    const fetchFn = setup().mockResolvedValueOnce(response([mockRecord]));
    const list = await fetchExternalIndicators();
    expect(list).toHaveLength(1);
    expect(list[0].name).toBe('Sentiment');
    expect(list[0].values[0].name).toBe('Score');
    expect(list[0].timeframe).toBe('D1');
    expect(list[0].dateFrom).toBe('2026-01-01');
    expect(list[0].totalDays).toBe(10);
    expect(fetchFn).toHaveBeenCalledWith(
      expect.stringContaining('/custom-data'),
      expect.objectContaining({ method: 'GET' }),
    );
  });

  it('saves and edits external indicators with formatted values', async () => {
    const fetchFn = setup().mockResolvedValueOnce(response(mockRecord));
    const def = toExternalIndicatorDefinition(mockRecord);
    const saved = await saveExternalIndicator(def);
    expect(saved.name).toBe('Sentiment');
    expect(JSON.parse(String(fetchFn.mock.calls[0][1].body))).toEqual({
      name: 'Sentiment',
      values: [{ name: 'Score', mt4: '0', mt5: '0', el: '0' }],
      data_type: 'custom',
      timeframe: 'D1',
    });

    fetchFn.mockResolvedValueOnce(response({ ...mockRecord, name: 'SentimentV2' }));
    const edited = await editExternalIndicator('Sentiment', { ...def, name: 'SentimentV2' });
    expect(edited.name).toBe('SentimentV2');
    expect(JSON.parse(String(fetchFn.mock.calls[1][1].body))).toEqual({
      indicator_name: 'Sentiment',
      name: 'SentimentV2',
      values: [{ name: 'Score', mt4: '0', mt5: '0', el: '0' }],
      data_type: 'custom',
      timeframe: 'D1',
    });
  });

  it('deletes and clears external indicators', async () => {
    const fetchFn = setup().mockResolvedValueOnce(
      response({ names: ['Sentiment'], cleared_records: 10, deleted_count: 1 }),
    );
    const deleted = await deleteExternalIndicators(['Sentiment']);
    expect(deleted).toEqual(['Sentiment']);
    expect(JSON.parse(String(fetchFn.mock.calls[0][1].body))).toEqual({ names: ['Sentiment'] });

    fetchFn.mockResolvedValueOnce(response({ names: ['Sentiment'], cleared_records: 10 }));
    const cleared = await clearExternalIndicators(['Sentiment']);
    expect(cleared.cleared_records).toBe(10);
  });

  it('reviews data with pagination', async () => {
    const fetchFn = setup().mockResolvedValueOnce(
      response({
        name: 'Sentiment',
        columns: ['Score'],
        records: [{ timestamp: '2026-01-01', values: { Score: 1.5 } }],
        pagination: { total: 1, limit: 100, offset: 0 },
      }),
    );
    const review = await fetchExternalReview('Sentiment', 50, 10);
    expect(review.name).toBe('Sentiment');
    expect(review.columns).toEqual(['Score']);
    expect(fetchFn).toHaveBeenCalledWith(
      expect.stringContaining('/custom-data/review?name=Sentiment&limit=50&offset=10'),
      expect.objectContaining({ method: 'GET' }),
    );
  });

  it('handles format presets and import info', async () => {
    const fetchFn = setup().mockResolvedValueOnce(
      response({
        formats: [{ name: 'CustomCSV', separator: ';', skip_rows: 1, skip_columns: 0, date_format: 'yyyy-MM-dd' }],
        separators: [',', ';'],
        date_formats: ['yyyy-MM-dd'],
        error_handling: ['abort', 'skip'],
        column_types: ['date', 'Score'],
        encoding: 'utf-8-sig',
      }),
    );
    const info = await fetchExternalImportInfo();
    expect(info.formats).toHaveLength(1);
    expect(info.formats[0].name).toBe('CustomCSV');
    expect(info.formats[0].separator).toBe(';');

    fetchFn.mockResolvedValueOnce(
      response({ name: 'CustomCSV', separator: ';', skip_rows: 1, skip_columns: 0, date_format: 'yyyy-MM-dd' }),
    );
    const savedFormat = await saveExternalImportFormat(info.formats[0], false);
    expect(savedFormat.name).toBe('CustomCSV');

    fetchFn.mockResolvedValueOnce(response({}));
    await deleteExternalImportFormat('CustomCSV');
    expect(fetchFn.mock.calls[2][0]).toContain('/custom-data/formats/CustomCSV');
  });

  it('handles import, preview, and recognize operations', async () => {
    const fetchFn = setup().mockResolvedValueOnce(
      response({ name: 'Sentiment', imported_count: 5, skipped_rows: 0, errors: [] }),
    );
    await importExternalIndicatorData('Sentiment', '2026-01-01,10', 'CustomCSV', false);
    expect(fetchFn).toHaveBeenCalledWith(
      expect.stringContaining('/custom-data/import'),
      expect.objectContaining({ method: 'POST' }),
    );

    fetchFn.mockResolvedValueOnce(
      response({
        name: 'Sentiment',
        total_records: 1,
        records: [{ timestamp: '2026-01-01', values: { Score: 10 } }],
        format: {},
      }),
    );
    const preview = await previewExternalIndicatorImport('Sentiment', '2026-01-01,10', 'CustomCSV');
    expect(preview.total_records).toBe(1);

    fetchFn.mockResolvedValueOnce(response(mockRecord));
    const recognized = await recognizeExternalIndicator('Sentiment.mq4', 'content');
    expect(recognized.name).toBe('Sentiment');
  });

  it('handles file export, definition save/load, and COT update', async () => {
    const fetchFn = setup().mockResolvedValueOnce(response({ content: 'date,Score\n2026-01-01,10', count: 1 }));
    const exported = await exportExternalIndicatorValues('Sentiment');
    expect(exported.count).toBe(1);

    fetchFn.mockResolvedValueOnce(response({ content: '{"version":1}', count: 1 }));
    const saved = await saveExternalDefinitions(['Sentiment']);
    expect(saved.count).toBe(1);

    fetchFn.mockResolvedValueOnce(response({ loaded: [mockRecord], loaded_count: 1, skipped: [] }));
    const loaded = await loadExternalDefinitions('{"version":1}', 'overwrite');
    expect(loaded.loaded_count).toBe(1);

    fetchFn.mockResolvedValueOnce(response({ updated_count: 2, records: 100, years: [2026] }));
    const cot = await updateCotIndicators([2026]);
    expect(cot.updated_count).toBe(2);
  });

  it('manages background jobs', async () => {
    const fetchFn = setup().mockResolvedValueOnce(
      response({ job_id: 'job-1', kind: 'custom.import', status: 'RUNNING', progress: 50 }),
    );
    const job = await fetchExternalImportJob('job-1');
    expect(job.status).toBe('RUNNING');

    fetchFn.mockResolvedValueOnce(
      response({ job_id: 'job-1', kind: 'custom.import', status: 'PAUSED', progress: 50 }),
    );
    const controlled = await controlExternalImportJob('job-1', 'pause');
    expect(controlled.status).toBe('PAUSED');
  });

  it('syncs remote indicators and format presets into store', async () => {
    setup()
      .mockResolvedValueOnce(response([mockRecord]))
      .mockResolvedValueOnce(
        response({
          formats: [
            {
              name: 'RemoteFormat',
              separator: ',',
              skip_rows: 0,
              skip_columns: 0,
              date_format: 'yyyy-MM-dd',
              columns: ['Date', 'Value 1'],
            },
          ],
          separators: [','],
          date_formats: ['yyyy-MM-dd'],
          error_handling: ['abort'],
          column_types: [],
          encoding: 'utf-8',
        }),
      );

    await useExternalIndicators.getState().syncRemote();
    const state = useExternalIndicators.getState();
    expect(state.definitions).toHaveLength(1);
    expect(state.definitions[0].name).toBe('Sentiment');
    expect(state.formats).toHaveLength(1);
    expect(state.formats[0].name).toBe('RemoteFormat');
  });

  it('dispatches store add, edit, clear, remove, and format changes to the client', async () => {
    const fetchFn = setup();
    // add
    fetchFn.mockResolvedValueOnce(response(mockRecord));
    await useExternalIndicators.getState().add(toExternalIndicatorDefinition(mockRecord));
    expect(fetchFn).toHaveBeenCalledWith(
      expect.stringContaining('/custom-data'),
      expect.objectContaining({ method: 'POST' }),
    );

    // edit
    fetchFn.mockResolvedValueOnce(response(mockRecord));
    await useExternalIndicators.getState().edit('Sentiment', toExternalIndicatorDefinition(mockRecord));
    expect(fetchFn).toHaveBeenCalledWith(
      expect.stringContaining('/custom-data/edit'),
      expect.objectContaining({ method: 'POST' }),
    );

    // clear
    fetchFn.mockResolvedValueOnce(response({ names: ['Sentiment'], cleared_records: 0 }));
    await useExternalIndicators.getState().clear(['Sentiment']);
    expect(fetchFn).toHaveBeenCalledWith(
      expect.stringContaining('/custom-data/clear'),
      expect.objectContaining({ method: 'POST' }),
    );

    // remove
    fetchFn.mockResolvedValueOnce(response({ names: ['Sentiment'], cleared_records: 0, deleted_count: 1 }));
    await useExternalIndicators.getState().remove(['Sentiment']);
    expect(fetchFn).toHaveBeenCalledWith(
      expect.stringContaining('/custom-data/delete'),
      expect.objectContaining({ method: 'POST' }),
    );
  });
});
