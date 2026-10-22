import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { catalogue, categories, filterCatalogue, parseCatalogue } from '../../../../../app/plugins/data_source/Dukascopy/dukascopy';
describe('Dukascopy donor catalogue', () => {
  it('loads every symbol in source order and preserves distinct date ranges', () => {
    expect(catalogue).toHaveLength(725);
    expect(catalogue.slice(0, 3).map(row => row.symbol)).toEqual(['AUDUSD', 'EURUSD', 'GBPUSD']);
    expect(catalogue.find(row => row.symbol === 'AUDCAD')).toMatchObject({ dateFrom: '2006-01-03', dateFromM1: '2007-03-13', fullCategory: 'Forex - Crosses' });
    expect(new Set(catalogue.map(row => row.symbol)).size).toBe(725);
  });
  it('filters names and categories without reordering', () => {
    expect(filterCatalogue('aud', 'Forex - Majors').map(row => row.symbol)).toEqual(['AUDUSD']);
    expect(filterCatalogue('no-such-symbol', '')).toEqual([]);
    expect(categories.slice(0, 3)).toEqual([{ value: '', name: 'All' }, { value: 'Forex', name: 'Forex - All' }, { value: 'Forex - Majors', name: 'Forex - Majors' }]);
  });
  it('rejects malformed catalogue rows', () => {
    expect(() => parseCatalogue('broken')).toThrow();
    expect(() => parseCatalogue('X;X;Forex;Majors;31.02.2020;01.01.2020;5;1;2;3;4;3')).toThrow();
  });
});


import { createDomainClient } from '../../../../../app/host/transport';
import { DukascopyRegistrationError, setDataClient, useDataManagerStore } from '../../../../../app/plugins/data_source/Common/dataManagerStore';
import type { AddDukasRequest } from '../../../../../app/plugins/data_source/Dukascopy/dukascopy';

describe('Dukascopy host registration', () => {
  const request: AddDukasRequest = { symbols: ['EURUSD'], dataType: 'M1', broker: '-1', postfix: '_TEST', instruments: ['-1'] };
  let rows: Array<Record<string, unknown>>;
  let failSymbol = '';
  let loseResponse = false;
  let malformed = false;
  let failRefresh = false;
  let posts: Array<Record<string, unknown>>;
  const install = () => {
    const fetchFn = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
      if (init?.method === 'POST') {
        const body = JSON.parse(String(init.body));
        posts.push(body);
        if (body.symbol === failSymbol) return new Response(JSON.stringify({status: 'error', error: {code: 'STORAGE', message: 'Storage unavailable'}}), {status: 503});
        const row = { ...body, id: `dukascopy:${body.symbol}:${body.timeframe}`, broker: 'default', broker_name: 'Default', timezone: 'UTC', instrument: body.underlying, bars: 0, category: 'Forex', path: 'data/market/dukascopy/m1/eurusd' };
        rows.push(row);
        if (loseResponse) throw new Error('Response lost');
        return new Response(JSON.stringify({status: 'success', data: malformed ? {...row, id: 'wrong'} : row}), {status: 201});
      }
      if (failRefresh && posts.length) throw new Error('Refresh unavailable');
      return new Response(JSON.stringify({status: 'success', data: rows}));
    });
    setDataClient(createDomainClient('/data', {baseUrl: 'http://localhost/api/v1', fetchFn}));
    return fetchFn;
  };
  beforeEach(() => {
    rows = []; posts = []; failSymbol = ''; loseResponse = false; malformed = false; failRefresh = false;
    useDataManagerStore.setState({definitions: [], savedDatasets: [], catalogError: '', storageError: 'Broken legacy browser storage', brokers: []});
    install();
  });
  afterEach(() => { vi.useRealTimers(); setDataClient(createDomainClient('/data')); });
  it('persists canonical requests and reloads the authoritative catalog without browser writes', async () => {
    await useDataManagerStore.getState().addData(request);
    expect(posts).toEqual([{source: 'dukascopy', symbol: 'EURUSD_TEST', underlying: 'EURUSD', timeframe: 'M1', broker: '-1', instrument: '-1'}]);
    expect(useDataManagerStore.getState().savedDatasets?.[0]).toMatchObject({id: 'dukascopy:EURUSD_TEST:M1', symbol: 'EURUSD_TEST', bars: 0});
    await expect(useDataManagerStore.getState().addData(request)).rejects.toThrow('already exists');
    expect(posts).toHaveLength(1);
  });
  it('rejects host failures without creating phantom rows', async () => {
    failSymbol = 'EURUSD_TEST';
    await expect(useDataManagerStore.getState().addData(request)).rejects.toThrow('0 of 1 symbols confirmed');
    expect(useDataManagerStore.getState().savedDatasets).toEqual([]);
    expect(useDataManagerStore.getState().definitions).toEqual([]);
  });
  it('reports partial completion and supports retrying only outstanding symbols', async () => {
    failSymbol = 'GBPUSD_TEST';
    const multi = {...request, symbols: ['EURUSD', 'GBPUSD'], instruments: ['-1', '-1']};
    let error: DukascopyRegistrationError | undefined;
    try { await useDataManagerStore.getState().addData(multi); } catch (cause) { error = cause as DukascopyRegistrationError; }
    expect(error?.confirmedSymbols).toEqual(['EURUSD']);
    expect(error?.message).toContain('1 of 2');
    expect(useDataManagerStore.getState().savedDatasets).toHaveLength(1);
    failSymbol = '';
    await useDataManagerStore.getState().addData({...request, symbols: ['GBPUSD']});
    expect(useDataManagerStore.getState().savedDatasets).toHaveLength(2);
  });
  it('reconciles an ambiguous network failure against persisted identities', async () => {
    loseResponse = true;
    await expect(useDataManagerStore.getState().addData(request)).rejects.toMatchObject({confirmedSymbols: ['EURUSD']});
    expect(useDataManagerStore.getState().savedDatasets).toHaveLength(1);
  });
  it('rejects malformed confirmations and reports catalog refresh failures', async () => {
    malformed = true;
    await expect(useDataManagerStore.getState().addData(request)).rejects.toThrow('did not confirm');
    rows = []; posts = []; malformed = false; failRefresh = true;
    await expect(useDataManagerStore.getState().addData(request)).rejects.toMatchObject({confirmedSymbols: ['EURUSD']});
    expect(useDataManagerStore.getState().catalogError).toContain('Unable to reconcile');
  });
  it('bounds a stalled host request and releases the registration guard', async () => {
    vi.useFakeTimers();
    setDataClient(createDomainClient('/data', {fetchFn: () => new Promise<Response>(() => {})}));
    const pending = useDataManagerStore.getState().addData(request);
    const rejection = expect(pending).rejects.toThrow('timed out');
    await vi.advanceTimersByTimeAsync(30000);
    await rejection;
    expect(posts).toHaveLength(0);
    install();
    await useDataManagerStore.getState().addData(request);
    expect(posts).toHaveLength(1);
  });
  it('guards re-entry while registration is pending', async () => {
    let resolve!: (value: Response) => void;
    const fetchFn = vi.fn(() => new Promise<Response>(done => { resolve = done; }));
    setDataClient(createDomainClient('/data', {fetchFn}));
    const pending = useDataManagerStore.getState().addData(request);
    await expect(useDataManagerStore.getState().addData(request)).rejects.toThrow('already running');
    resolve(new Response(JSON.stringify({status: 'success', data: []})));
    setDataClient(createDomainClient('/data', {fetchFn: vi.fn().mockRejectedValue(new Error('Stopped test'))}));
    await expect(pending).rejects.toThrow('Stopped test');
  });
});


import { createElement } from 'react';
import * as dukascopyService from '../../../../../app/plugins/data_source/Dukascopy/DukascopyService';
import { renderToStaticMarkup } from 'react-dom/server';
import { AddPopup } from '../../../../../app/plugins/data_source/Dukascopy/add/addPopup';

describe('Dukascopy saved broker presentation', () => {
  beforeEach(() => {
    vi.spyOn(dukascopyService, 'useDukascopyAddService').mockImplementation(() => {
      const state = useDataManagerStore.getState();
      return {brokers: state.brokers, brokerLoading: state.brokerLoading, brokerError: state.brokerError,
        reloadBrokers: state.syncBrokers, addData: state.addData};
    });
  });
  const render = () => renderToStaticMarkup(createElement(AddPopup, {open: true, onClose: () => {}, onComplete: () => {}}));
  afterEach(() => {vi.restoreAllMocks(); useDataManagerStore.setState({brokers: [], brokerLoading: false, brokerError: ''});});
  it('shows eligible and disabled saved brokers from the shared table store', () => {
    useDataManagerStore.setState({brokerLoading: false, brokerError: '', brokers: [
      {id: '2', name: '[[Saved broker]]', postfix: '_S', timezone: 'UTC', mtUse: true, desc: '', stockPickerUse: false, system: false, stocks: [], instruments: []},
      {id: '3', name: 'Disabled broker', postfix: '', timezone: 'UTC', mtUse: false, desc: '', stockPickerUse: false, system: false, stocks: [], instruments: []},
    ]});
    const html = render();
    expect(html).toContain('>Saved broker</option>');
    expect(html).not.toContain('[[Saved broker]]');
    expect(useDataManagerStore.getState().brokers[0].name).toBe('[[Saved broker]]');
    expect(html).toContain('value="3" disabled=""');
    expect(html).toContain('Disabled broker (disabled for data management)');
  });
  it('distinguishes a loading catalog, a failed load and a successful empty catalog', () => {
    useDataManagerStore.setState({brokers: [], brokerLoading: true, brokerError: ''});
    expect(render()).toContain('Loading broker profiles...');
    expect(render()).not.toContain('No saved broker profiles.');
    useDataManagerStore.setState({brokerLoading: false, brokerError: 'Broker load failed'});
    expect(render()).toContain('Broker load failed');
    expect(render()).toContain('Retry broker profiles');
    useDataManagerStore.setState({brokerError: ''});
    expect(render()).toContain('No saved broker profiles. Default is available.');
  });
});
