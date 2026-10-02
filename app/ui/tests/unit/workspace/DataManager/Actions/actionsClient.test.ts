import { beforeEach, describe, expect, it, vi } from 'vitest';
import { actionsClient, downloadBlob, datasetBarLabel, datasetTypeLabel, datasetTimezoneLabel, type DatasetRow } from '../../../../../app/workspace/DataManager/Actions/actionsClient';
import { formatDeleteCompletion, getDeleteConfirmMessage } from '../../../../../app/workspace/DataManager/Actions/MassDeleteDialog';

const mockPost = vi.fn();
vi.mock('../../../../../app/host/transport', () => ({
  createDomainClient: () => ({
    post: (url: string, payload: any) => mockPost(url, payload),
  }),
}));

describe('actionsClient', () => {
  it('requests an explicit clock observation for one dataset without changing its definition', async () => {
    mockPost.mockResolvedValueOnce({ offset_hours: 3, status: 'estimated' });
    expect(await actionsClient.detectMt5Timezone('dataset-id')).toEqual({ offset_hours: 3, status: 'estimated' });
    expect(mockPost).toHaveBeenCalledWith('/sources.meta_trader.detect_timezone', { dataset_id: 'dataset-id' });
  });
  beforeEach(() => {
    mockPost.mockReset();
  });

  it('invokes exportToCsv correctly', async () => {
    mockPost.mockResolvedValueOnce({
      success: true,
      symbol: 'EURUSD',
      timeframe: 'M5',
      records: 120,
      contentLength: 2048,
    });
    const res = await actionsClient.exportToCsv({
      symbol: 'EURUSD',
      timeframe: 'M5',
      date_from: '2025-01-01',
      date_to: '2025-01-02',
    });
    expect(mockPost).toHaveBeenCalledWith('/actions.export_to_csv', {
      symbol: 'EURUSD',
      timeframe: 'M5',
      date_from: '2025-01-01',
      date_to: '2025-01-02',
    });
    expect(res.records).toBe(120);
  });

  it('invokes exportToMt4 correctly', async () => {
    mockPost.mockResolvedValueOnce({
      success: true,
      symbol: 'EURUSD',
      files: ['EURUSD1.hst', 'EURUSD1_0.fxt'],
    });
    const res = await actionsClient.exportToMt4({
      symbol: 'EURUSD',
      timeframe: 'M1',
      spread: 20,
    });
    expect(mockPost).toHaveBeenCalledWith('/actions.export_to_mt4', {
      symbol: 'EURUSD',
      timeframe: 'M1',
      spread: 20,
    });
    expect(res.files).toHaveLength(2);
  });

  it('invokes exportToMt5 correctly', async () => {
    mockPost.mockResolvedValueOnce({
      success: true,
      symbol: 'EURUSD',
      kind: 'm1',
      timeframe: 'M1',
      records: 50,
    });
    const res = await actionsClient.exportToMt5({
      symbol: 'EURUSD',
      timeframe: 'M1',
      spread_mode: 'real',
    });
    expect(mockPost).toHaveBeenCalledWith('/actions.export_to_mt5', {
      symbol: 'EURUSD',
      timeframe: 'M1',
      spread_mode: 'real',
    });
    expect(res.records).toBe(50);
  });

  it('invokes cloneToTimezone correctly', async () => {
    mockPost.mockResolvedValueOnce({
      success: true,
      sourceSymbol: 'EURUSD',
      clonedSymbol: 'EURUSD_M1_UTC+2',
      bars: 500,
    });
    const res = await actionsClient.cloneToTimezone({
      symbol: 'EURUSD',
      shift_hours: 2,
      remove_weekends: true,
    });
    expect(mockPost).toHaveBeenCalledWith('/actions.clone_to_timezone', {
      symbol: 'EURUSD',
      shift_hours: 2,
      remove_weekends: true,
    });
    expect(res.clonedSymbol).toBe('EURUSD_M1_UTC+2');
  });

  it('invokes deleteDatasets correctly', async () => {
    mockPost.mockResolvedValueOnce({
      success: true,
      deletedCount: 2,
      mode: 'remove',
      deleted: ['SYM1', 'SYM2'],
    });
    const res = await actionsClient.deleteDatasets({
      symbols: ['SYM1', 'SYM2'],
      mode: 'remove',
    });
    expect(mockPost).toHaveBeenCalledWith('/actions.delete', {
      symbols: ['SYM1', 'SYM2'],
      mode: 'remove',
    });
    expect(res.deletedCount).toBe(2);
    expect(formatDeleteCompletion(res, 'remove')).toBe('Deleted 2 dataset(s): SYM1, SYM2.');
  });

  it('formats the running backend delete response without a symbol list', async () => {
    mockPost.mockResolvedValueOnce({ success: true, affected: 1, mode: 'remove' });
    const res = await actionsClient.deleteDatasets({
      symbols: ['SYM1'],
      mode: 'remove',
    });
    expect(formatDeleteCompletion(res, 'remove')).toBe('Deleted 1 dataset(s).');
    expect(formatDeleteCompletion(res, 'clear')).toBe('Cleared data for 1 dataset(s).');
  });

  it('rejects an unsuccessful or malformed delete response', () => {
    expect(() => formatDeleteCompletion({ success: false, mode: 'remove', affected: 1 }, 'remove'))
      .toThrow('Dataset deletion did not succeed.');
    expect(() => formatDeleteCompletion({ success: true, mode: 'remove' }, 'remove'))
      .toThrow('Invalid dataset deletion response.');
  });

  it('invokes saveDefinitions and loadDefinitions correctly', async () => {
    mockPost.mockResolvedValueOnce({
      success: true,
      datasetsCount: 5,
      instrumentsCount: 3,
      content: '{"datasets":[]}',
    });
    const saveRes = await actionsClient.saveDefinitions({ symbols: ['EURUSD'] });
    expect(mockPost).toHaveBeenCalledWith('/actions.save', { symbols: ['EURUSD'] });
    expect(saveRes.datasetsCount).toBe(5);

    mockPost.mockResolvedValueOnce({
      success: true,
      loadedDatasets: 5,
      loadedInstruments: 3,
    });
    const loadRes = await actionsClient.loadDefinitions({
      definitions: [{ id: 'd1' }],
      instruments: [{ id: 'i1' }],
    });
    expect(mockPost).toHaveBeenCalledWith('/actions.load', {
      definitions: [{ id: 'd1' }],
      instruments: [{ id: 'i1' }],
    });
    expect(loadRes.loadedDatasets).toBe(5);
  });

  it('invokes review methods correctly', async () => {
    mockPost.mockResolvedValueOnce({
      symbol: 'EURUSD',
      timeframe: 'M1',
      totalRows: 1,
      offset: 0,
      limit: 10,
      rows: [['2025-01-01 00:00', 1.1, 1.2, 1.0, 1.15, 100]],
    });
    const dataRes = await actionsClient.reviewData({ symbol: 'EURUSD', offset: 0, limit: 10 });
    expect(mockPost).toHaveBeenCalledWith('/actions.review_data', { symbol: 'EURUSD', offset: 0, limit: 10 });
    expect(dataRes.rows).toHaveLength(1);

    mockPost.mockResolvedValueOnce({
      symbol: 'EURUSD',
      timeframe: 'M1',
      count: 1,
      chart: [{ time: 1700000000000, open: 1.1, high: 1.2, low: 1.0, close: 1.15, volume: 100 }],
    });
    const chartRes = await actionsClient.reviewChart({ symbol: 'EURUSD', limit: 50 });
    expect(mockPost).toHaveBeenCalledWith('/actions.review_chart', { symbol: 'EURUSD', limit: 50 });
    expect(chartRes.chart).toHaveLength(1);

    mockPost.mockResolvedValueOnce({
      symbol: 'EURUSD',
      timeframe: 'M1',
      totalBars: 1000,
      totalErrors: 2,
      qualityScore: 98.5,
      problems: [{ date: '2025-01-01', problem: 'Gap of 120m' }],
    });
    const qualityRes = await actionsClient.reviewQuality({ symbol: 'EURUSD' });
    expect(mockPost).toHaveBeenCalledWith('/actions.review_quality', { symbol: 'EURUSD' });
    expect(qualityRes.qualityScore).toBe(98.5);
  });

  it('invokes updateAll and updateSelected correctly', async () => {
    mockPost.mockResolvedValueOnce({ success: true, datasets: [], queued: 3 });
    const allRes = await actionsClient.updateAll({ provider: 'dukascopy' });
    expect(mockPost).toHaveBeenCalledWith('/actions.update_all', { provider: 'dukascopy' });
    expect(allRes.queued).toBe(3);

    mockPost.mockResolvedValueOnce({ success: true, datasets: [], queued: 1 });
    const selRes = await actionsClient.updateSelected({ symbols: ['EURUSD'] });
    expect(mockPost).toHaveBeenCalledWith('/actions.update_selected', { symbols: ['EURUSD'] });
    expect(selRes.queued).toBe(1);
  });

  it('invokes brokerData and brokerDataUpdate correctly', async () => {
    mockPost.mockResolvedValueOnce({ query: 'EUR', count: 1, instruments: [] });
    const bData = await actionsClient.brokerData({ query: 'EUR' });
    expect(mockPost).toHaveBeenCalledWith('/actions.broker_data', { query: 'EUR' });
    expect(bData.query).toBe('EUR');

    mockPost.mockResolvedValueOnce({ success: true, updatedDatasets: 4, brokerProfiles: 2 });
    const bUpdate = await actionsClient.brokerDataUpdate();
    expect(mockPost).toHaveBeenCalledWith('/actions.broker_data_update', {});
    expect(bUpdate.updatedDatasets).toBe(4);
  });

  it('executes downloadBlob cleanly in DOM and non-DOM environment', () => {
    // In node environment, document is undefined, so it returns early safely
    expect(() => downloadBlob('test.txt', 'hello world', 'text/plain')).not.toThrow();

    const mockClick = vi.fn();
    const mockRemove = vi.fn();
    const mockAnchor = { href: '', download: '', click: mockClick, remove: mockRemove };
    const mockCreateElement = vi.fn().mockReturnValue(mockAnchor);
    const mockAppendChild = vi.fn();
    const mockRemoveChild = vi.fn();

    const origDoc = (globalThis as any).document;
    const origUrl = (globalThis as any).URL;
    try {
      (globalThis as any).document = {
        createElement: mockCreateElement,
        body: { appendChild: mockAppendChild, removeChild: mockRemoveChild },
      };
      (globalThis as any).URL = {
        createObjectURL: vi.fn().mockReturnValue('blob:mock-url'),
        revokeObjectURL: vi.fn(),
      };

      downloadBlob('test.csv', 'col1,col2', 'text/csv');
      expect(mockCreateElement).toHaveBeenCalledWith('a');
      expect(mockAppendChild).toHaveBeenCalledWith(mockAnchor);
      expect(mockClick).toHaveBeenCalled();
      expect(mockRemove).toHaveBeenCalled();
    } finally {
      (globalThis as any).document = origDoc;
      (globalThis as any).URL = origUrl;
    }
  });

  it('formats delete confirm message in accordance with specification', () => {
    expect(getDeleteConfirmMessage([])).toBe('No symbols selected.');
    expect(getDeleteConfirmMessage(['EURUSD'])).toBe(
      "Do you want to remove symbol 'EURUSD' or only clear its data ?",
    );
    expect(getDeleteConfirmMessage(['EURUSD', 'GBPUSD', 'USDJPY'])).toBe(
      'Do you want to remove selected symbols (3) or only clear their data ?',
    );
    expect(
      getDeleteConfirmMessage(['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8']),
    ).toBe('Do you want to remove selected symbols (8) or only clear their data ?');
  });

  it('invokes listDatasets correctly', async () => {
    mockPost.mockResolvedValueOnce([
      {
        id: 'ds-1',
        source: 'Dukascopy',
        symbol: 'EURUSD_dukascopy',
        underlying: 'EURUSD',
        instrument: 'EURUSD',
        timeframe: 'M1',
        broker: '3',
        brokerName: 'Dukascopy',
        timezone: 'UTC',
        category: 'Forex',
        from: '2026-01-01',
        to: '2026-01-02',
        bars: 1000,
        quality: 100.0,
        status: 'Ready',
      },
    ]);
    const res = await actionsClient.listDatasets();
    expect(mockPost).toHaveBeenCalledWith('/actions.list_datasets', {});
    expect(res).toHaveLength(1);
    expect(res[0].symbol).toBe('EURUSD_dukascopy');
  });
});

const row: DatasetRow = { id: 'fixture', source: 'MT5', symbol: 'XAUUSD', underlying: 'XAUUSD', instrument: 'XAUUSD', timeframe: 'M1', broker: '6', brokerName: 'Pepperstone', timezone: 'UTC', category: 'Markets-Commodities-Gold', from: '', to: '', bars: 0 };

describe('authoritative dataset presentation', () => {
  it('distinguishes unknown bar convention from end of bar', () => {
    expect(datasetBarLabel(row)).toBe('—');
    expect(datasetBarLabel({ ...row, barType: 'start' })).toBe('Start of Bar');
    expect(datasetBarLabel({ ...row, barType: 'end' })).toBe('End of Bar');
  });
  it('uses instrument type separately from folder category', () => {
    expect(datasetTypeLabel({ ...row, dataType: 'CFD' })).toBe('CFD');
    expect(datasetTypeLabel({ ...row, source: 'Dukascopy' })).toBe(row.category);
  });
  it('never presents a current broker estimate as normalized historical data', () => {
    const estimated = { ...row, clockStatus: 'estimated' as const, brokerUtcOffset: 3 };
    expect(datasetTimezoneLabel(estimated)).toBe('Exchange/Broker');
    expect(datasetTimezoneLabel({ ...estimated, clockStatus: 'expired' })).toBe('Exchange/Broker');
    expect(datasetTimezoneLabel({ ...estimated, clockNormalization: 'broker_time' })).toBe('Exchange/Broker');
    expect(datasetTimezoneLabel({ ...estimated, clockNormalization: 'normalized' })).toBe('UTC');
    expect(datasetTimezoneLabel({ ...row, source: 'Yahoo' })).toBe('UTC');
  });
});
