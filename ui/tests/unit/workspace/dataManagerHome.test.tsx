import { renderToString } from 'react-dom/server';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createDomainClient } from '../../../app/host/transport';
import { DataManagerHome } from '../../../app/workspace/DataManager/DataManagerHome';
import {
  fetchRemoteDatasets,
  setDataClient,
  useDataManagerStore,
  type MockDefinition,
} from '../../../app/plugins/data_source/Common/dataManagerStore';

describe('DataManagerHome component and store wiring', () => {
  const memory = new Map<string, string>();
  const storage = {
    getItem: (key: string) => memory.get(key) ?? null,
    setItem: (key: string, value: string) => { memory.set(key, value); },
    removeItem: (key: string) => memory.delete(key),
    clear: () => memory.clear(),
  };

  beforeEach(() => {
    vi.restoreAllMocks();
    memory.clear();
    vi.stubGlobal('localStorage', storage);
    useDataManagerStore.setState({ definitions: [], savedDatasets: null, catalogLoading: false, catalogError: '', brokers: [], brokerJob: null, storageError: '' });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders home header, status indicators, and section headings', () => {
    const html = renderToString(<DataManagerHome />);

    expect(html).toContain('Data Manager Home');
    expect(html).toContain('HaruQuantAI Market Data Engine');
    expect(html).toContain('Partitioned Parquet (ZSTD lvl 6)');
    expect(html).toContain('SQLite (datamgr_datasets)');
    expect(html).toContain('Catalog Overview Metrics');
    expect(html).toContain('Quick Actions');
    expect(html).toContain('Saved Datasets Catalog');
    expect(html).toContain('SQLite datamgr_datasets');
  });

  it('renders all 6 overview metric cards', () => {
    const html = renderToString(<DataManagerHome />);

    expect(html).toContain('Total Datasets');
    expect(html).toContain('Historical Bars (M1/Ticks)');
    expect(html).toContain('Instruments');
    expect(html).toContain('Trading Sessions');
    expect(html).toContain('Active Providers');
    expect(html).toContain('Custom Baskets');
  });

  it('renders quick action buttons with descriptive labels', () => {
    const html = renderToString(<DataManagerHome />);

    expect(html).toContain('Import Market Data');
    expect(html).toContain('Download Online Data');
    expect(html).toContain('Configure Instruments');
    expect(html).toContain('Trading Sessions');
  });

  it('renders saved datasets catalog table headers and columns', () => {
    const html = renderToString(<DataManagerHome />);

    expect(html).toContain('Symbol Name');
    expect(html).toContain('Instrument');
    expect(html).toContain('Broker profile');
    expect(html).toContain('Underlying Symbol');
    expect(html).toContain('Timeframe');
    expect(html).toContain('Timezone');
    expect(html).toContain('Date from');
    expect(html).toContain('Date to');
    expect(html).toContain('Total Days');
    expect(html).toContain('Total Records');
    expect(html).toContain('Source');
    expect(html).toContain('Data type');
  });

  it('fetches remote datasets and maps fields accurately', async () => {
    const mockApiResponse = {
      status: 'success',
      data: [
        {
          id: 'ds_dukascopy_EURUSD_M1',
          symbol: 'EURUSD',
          timeframe: 'M1',
          broker: 'Dukascopy',
          source: 'dukascopy',
          timezone: 'UTC',
          bars: 125000,
          date_from: '2025-01-01',
          date_to: '2025-04-01',
          category: 'Forex',
          total_days: 90,
          total_records: 125000,
          broker_name: 'Dukascopy Broker',
          underlying: 'EUR/USD Spot',
          instrument: 'EURUSD.fx',
          path: 'data/history/dukascopy/EURUSD/M1.parquet',
          bar_type: 'end',
        },
      ],
    };

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockApiResponse,
    } as Response);

    setDataClient(createDomainClient('/data', {
      baseUrl: 'http://localhost/api/v1',
      fetchFn: mockFetch as any,
    }));

    const datasets = await fetchRemoteDatasets();
    expect(datasets).toHaveLength(1);
    expect(datasets[0]).toMatchObject({
      id: 'ds_dukascopy_EURUSD_M1',
      symbol: 'EURUSD',
      timeframe: 'M1',
      source: 'dukascopy',
      bars: 125000,
      from: '2025-01-01',
      to: '2025-04-01',
      category: 'Forex',
      totalDays: 90,
      brokerName: 'Dukascopy Broker',
      underlying: 'EUR/USD Spot',
      instrument: 'EURUSD.fx',
      path: 'data/history/dukascopy/EURUSD/M1.parquet',
      barType: 'end',
    });
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost/api/v1/data/home/datasets',
      expect.objectContaining({ method: 'GET' }),
    );
  });

  it('syncs remote datasets into store and updates existing bar counts', async () => {
    const initialDef: MockDefinition = {
      id: 'ds_dukascopy_EURUSD_M1',
      source: 'dukascopy',
      symbol: 'EURUSD',
      underlying: 'EURUSD',
      instrument: 'EURUSD',
      timeframe: 'M1',
      broker: 'Dukascopy',
      brokerName: 'Dukascopy',
      timezone: 'UTC',
      category: 'Forex',
      from: '2025-01-01',
      to: '2025-01-31',
      bars: 50000,
    };

    useDataManagerStore.setState({
      definitions: [initialDef],
      brokers: [],
      brokerJob: null,
      storageError: '',
    });

    const mockApiResponse = {
      status: 'success',
      data: [
        {
          id: 'ds_dukascopy_EURUSD_M1',
          symbol: 'EURUSD',
          timeframe: 'M1',
          broker: 'Dukascopy',
          source: 'dukascopy',
          timezone: 'UTC',
          bars: 125000,
          date_from: '2025-01-01',
          date_to: '2025-04-01',
          category: 'Forex',
        },
        {
          id: 'ds_dukascopy_GBPUSD_M1',
          symbol: 'GBPUSD',
          timeframe: 'M1',
          broker: 'Dukascopy',
          source: 'dukascopy',
          timezone: 'UTC',
          bars: 80000,
          date_from: '2025-01-01',
          date_to: '2025-03-01',
          category: 'Forex',
        },
      ],
    };

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockApiResponse,
    } as Response);

    setDataClient(createDomainClient('/data', {
      baseUrl: 'http://localhost/api/v1',
      fetchFn: mockFetch as any,
    }));

    await useDataManagerStore.getState().syncRemoteDatasets();

    const state = useDataManagerStore.getState();
    expect(state.definitions).toHaveLength(2);
    // Updated existing
    expect(state.definitions[0].bars).toBe(125000);
    expect(state.definitions[0].to).toBe('2025-04-01');
    // Appended new
    expect(state.definitions[1].id).toBe('ds_dukascopy_GBPUSD_M1');
    expect(state.definitions[1].bars).toBe(80000);
    expect(state.savedDatasets).toEqual(state.definitions);
    expect(state.savedDatasets?.[0]).not.toBe(state.definitions[0]);
    expect(state.catalogLoading).toBe(false);
    expect(state.catalogError).toBe('');
  });

  it('clears both old server rows and cached definitions after an empty success', async () => {
    const row = { id: 'old', symbol: 'OLD' } as MockDefinition;
    useDataManagerStore.setState({ definitions: [row], savedDatasets: [row] });
    setDataClient(createDomainClient('/data', { fetchFn: vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: 'success', data: [] }))) }));
    await useDataManagerStore.getState().syncRemoteDatasets();
    expect(useDataManagerStore.getState()).toMatchObject({ definitions: [], savedDatasets: [], catalogError: '', catalogLoading: false });
  });

  it('surfaces initial failures without promoting cached definitions to the catalog', async () => {
    useDataManagerStore.setState({ definitions: [{ id: 'cached' } as MockDefinition] });
    setDataClient(createDomainClient('/data', { fetchFn: vi.fn().mockRejectedValue(new Error('Host unavailable')) }));
    await useDataManagerStore.getState().syncRemoteDatasets();
    expect(useDataManagerStore.getState()).toMatchObject({ savedDatasets: null, catalogError: 'Host unavailable', catalogLoading: false });
  });

  it('retains only the last server snapshot on malformed refresh and recovers on retry', async () => {
    const row = { id: 'server' } as MockDefinition;
    useDataManagerStore.setState({ savedDatasets: [row] });
    const fetchFn = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: 'success', data: {} })))
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: 'success', data: [] })));
    setDataClient(createDomainClient('/data', { fetchFn }));
    await useDataManagerStore.getState().syncRemoteDatasets();
    expect(useDataManagerStore.getState()).toMatchObject({ savedDatasets: [row], catalogError: 'Invalid saved dataset catalog response.' });
    await useDataManagerStore.getState().syncRemoteDatasets();
    expect(useDataManagerStore.getState()).toMatchObject({ savedDatasets: [], catalogError: '' });
  });

  it('ignores responses from superseded catalog requests', async () => {
    let finishOld: (response: Response) => void = () => { throw new Error('Request not started'); };
    const fetchFn = vi.fn()
      .mockImplementationOnce(() => new Promise<Response>(resolve => { finishOld = resolve; }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: 'success', data: [] })));
    setDataClient(createDomainClient('/data', { fetchFn }));
    const oldRequest = useDataManagerStore.getState().syncRemoteDatasets();
    expect(useDataManagerStore.getState().catalogLoading).toBe(true);
    await useDataManagerStore.getState().syncRemoteDatasets();
    finishOld(new Response(JSON.stringify({ status: 'success', data: [{ id: 'old', symbol: 'OLD', timeframe: 'M1' }] })));
    await oldRequest;
    expect(useDataManagerStore.getState()).toMatchObject({ savedDatasets: [], catalogError: '', catalogLoading: false });
  });

  it.each([[{}], [null], [{ id: 'invalid', symbol: 'INVALID', timeframe: 'M1', total_records: -1 }]])('rejects malformed catalog rows without publishing them: %j', async item => {
    setDataClient(createDomainClient('/data', { fetchFn: vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: 'success', data: [item] }))) }));
    await useDataManagerStore.getState().syncRemoteDatasets();
    expect(useDataManagerStore.getState()).toMatchObject({ savedDatasets: null, catalogError: 'Invalid saved dataset catalog response.', catalogLoading: false });
  });

  it('performs dataset edit, clear, and remove actions against backend API', async () => {
    const testDef: MockDefinition = {
      id: 'ds_test_1',
      source: 'test',
      symbol: 'TESTSYM',
      underlying: 'TESTSYM',
      instrument: 'TESTSYM',
      timeframe: 'M1',
      broker: 'default',
      brokerName: 'Default',
      timezone: 'UTC',
      category: 'Forex',
      from: '2025-01-01',
      to: '2025-01-31',
      bars: 1000,
    };

    useDataManagerStore.setState({
      definitions: [testDef],
      brokers: [],
      brokerJob: null,
      storageError: '',
    });

    const serverRow = { ...testDef, date_from: testDef.from, date_to: testDef.to, timezone: 'Europe/Prague', total_days: 30 };
    const response = (data: unknown) => new Response(JSON.stringify({ status: 'success', data }));
    const mockFetch = vi.fn()
      .mockResolvedValueOnce(response({ ok: true }))
      .mockResolvedValueOnce(response([serverRow]))
      .mockResolvedValueOnce(response({ ok: true }))
      .mockResolvedValueOnce(response([{ ...serverRow, bars: 0, date_from: '', date_to: '', total_days: 0 }]))
      .mockResolvedValueOnce(response({ ok: true }))
      .mockResolvedValueOnce(response([]));

    setDataClient(createDomainClient('/data', {
      baseUrl: 'http://localhost/api/v1',
      fetchFn: mockFetch as any,
    }));

    // Edit
    await useDataManagerStore.getState().editDataset('ds_test_1', { timezone: 'Europe/Prague' });
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost/api/v1/data/datasets/ds_test_1',
      expect.objectContaining({ method: 'PUT' }),
    );
    expect(useDataManagerStore.getState().definitions[0].timezone).toBe('Europe/Prague');
    expect(useDataManagerStore.getState().savedDatasets?.[0].timezone).toBe('Europe/Prague');

    // Clear
    await useDataManagerStore.getState().clearDataset('ds_test_1');
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost/api/v1/data/datasets/ds_test_1/clear',
      expect.objectContaining({ method: 'POST' }),
    );
    expect(useDataManagerStore.getState().definitions[0].bars).toBe(0);
    expect(useDataManagerStore.getState().savedDatasets?.[0].totalDays).toBe(0);

    // Remove
    await useDataManagerStore.getState().removeDataset('ds_test_1');
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost/api/v1/data/datasets/ds_test_1/delete',
      expect.objectContaining({ method: 'POST' }),
    );
    expect(useDataManagerStore.getState().definitions).toHaveLength(0);
    expect(useDataManagerStore.getState().savedDatasets).toEqual([]);
    expect(useDataManagerStore.getState().catalogError).toBe('');
  });

  it('replaces stale or synthetic local datasets with authoritative backend datasets', async () => {
    const staleSyntheticDef: MockDefinition = {
      id: 'broker-data:1:AAPL',
      source: 'Equity',
      symbol: 'AAPL',
      underlying: 'AAPL',
      instrument: 'AAPL',
      timeframe: 'D1',
      broker: '1',
      brokerName: 'XTB',
      timezone: 'UTC',
      category: 'Stock',
      from: '2026-10-10',
      to: '2026-10-10',
      bars: 1,
    };

    useDataManagerStore.setState({
      definitions: [staleSyntheticDef],
      brokers: [],
      brokerJob: null,
      storageError: '',
    });

    const realBackendDataset = {
      id: 'real_dataset_123',
      symbol: 'EURUSD',
      timeframe: 'M1',
      broker: 'Dukascopy',
      source: 'Dukascopy',
      timezone: 'UTC',
      bars: 500000,
      date_from: '2020-01-01',
      date_to: '2024-01-01',
      category: 'Forex',
    };

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        status: 'success',
        data: [realBackendDataset],
      }),
    } as Response);

    setDataClient(createDomainClient('/data', {
      baseUrl: 'http://localhost/api/v1',
      fetchFn: mockFetch as any,
    }));

    await useDataManagerStore.getState().syncRemoteDatasets();

    const state = useDataManagerStore.getState();
    expect(state.definitions).toHaveLength(1);
    expect(state.definitions[0].id).toBe('real_dataset_123');
    expect(state.definitions[0].symbol).toBe('EURUSD');
    expect(state.definitions[0].bars).toBe(500000);
    // Verified that synthetic item was eliminated
    expect(state.definitions.some(d => d.id.startsWith('broker-data:'))).toBe(false);
  });

  it('advances broker update without generating synthetic datasets', () => {
    useDataManagerStore.setState({
      definitions: [],
      brokers: [{
        id: '1',
        name: 'XTB',
        desc: '',
        postfix: '',
        timezone: 'UTC',
        mtUse: false,
        stockPickerUse: true,
        system: false,
        stocks: ['AAPL', 'MSFT'],
        instruments: [],
      }],
      brokerJob: {
        brokerIds: ['1'],
        state: 'running',
        progress: 90,
        targets: [
          { brokerId: '1', ticker: 'AAPL', symbol: 'AAPL' },
          { brokerId: '1', ticker: 'MSFT', symbol: 'MSFT' },
        ],
      },
      storageError: '',
    });

    useDataManagerStore.getState().advanceBrokerUpdate();

    const state = useDataManagerStore.getState();
    expect(state.brokerJob?.state).toBe('completed');
    expect(state.brokerJob?.progress).toBe(100);
    // Definitions must remain untouched, zero synthetic datasets generated
    expect(state.definitions).toHaveLength(0);
  });
});
