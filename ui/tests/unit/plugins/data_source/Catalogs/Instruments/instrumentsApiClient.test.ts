import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createDomainClient } from '../../../../../../app/host/transport';
import { defaultCommission, newInstrument } from '../../../../../../app/plugins/data_source/FileImport/fileSymbols';
import { fetchRemoteInstruments, fromFileInstrument, massEditRemoteInstruments, setInstrumentApiClient, toFileInstrument, type RemoteInstrumentDefinition } from '../../../../../../app/plugins/data_source/Catalogs/Instruments/instrumentsApiClient';
import { useInstruments } from '../../../../../../app/plugins/data_source/Catalogs/Instruments/instrumentsStore';

const row: RemoteInstrumentDefinition = {
  id: '1', symbol: 'RECORDED', broker_id: 0, description: 'Recorded specification', data_type: 'Forex',
  point_value: 12, point_size: .01, tick_size: .25, tick_step: .05, contract_size: 50, pip_size: .1,
  margin_rate: 0, decimals: 2, tick_value_in_money: 7, min_volume: 2, max_volume: 50, lot_step: 2,
  default_spread: 0, default_slippage: 0, min_distance: 0, order_size_multiplier: 1, order_size_step: 0,
  commissions: '4.75', swap_long: -1, swap_short: 2, swap_3day_day: 0, swap_settings: null,
};
const response = (data: unknown) => new Response(JSON.stringify({ status: 'success', data }));
function setup() {
  const fetchFn = vi.fn();
  setInstrumentApiClient(createDomainClient('/data', { fetchFn, baseUrl: '/api/v1' }));
  return fetchFn;
}
beforeEach(() => useInstruments.getState().reset());

describe('confirmed instrument transport and state', () => {
  it('preserves distinct economics, zero margins and the original raw record', () => {
    const item = toFileInstrument(row);
    expect(item).toMatchObject({ id: '1', broker: '0', marginRate: 0, tickSize: .25, tickStep: .05, contractSize: 50, minVolume: 2, tickValue: 7 });
    expect(item.record).toEqual(row);
    expect(fromFileInstrument(item)).toMatchObject({ broker_id: 0, margin_rate: 0, decimals: 2, contract_size: 50, max_volume: 50 });
    const commission = { ...defaultCommission('Per trade'), value: 6 };
    expect(toFileInstrument({ ...row, commissions: JSON.stringify({ version: 1, settings: commission }) }).commission).toEqual(commission);
  });

  it('does not reinterpret missing legacy sizes or cache an empty/error response', async () => {
    const fetchFn = setup().mockResolvedValueOnce(response([{ ...row, pip_size: null, contract_size: null }]))
      .mockResolvedValueOnce(response([])).mockRejectedValueOnce(new Error('offline'));
    await useInstruments.getState().refreshFromServer();
    expect(useInstruments.getState().instruments[0].contractSize).toBeNull();
    await useInstruments.getState().refreshFromServer();
    expect(useInstruments.getState().instruments).toEqual([]);
    await useInstruments.getState().refreshFromServer();
    expect(useInstruments.getState().error).toContain('offline');
    expect(fetchFn).toHaveBeenCalledTimes(3);
  });

  it('waits for add confirmation and never manufactures a clone after rejection', async () => {
    const fetchFn = setup();
    let resolve!: (value: Response) => void;
    fetchFn.mockReturnValueOnce(new Promise<Response>(done => { resolve = done; }));
    const pending = useInstruments.getState().addInstrument({ ...newInstrument(), symbol: 'RECORDED', contractSize: 50, pipSize: .1 });
    expect(useInstruments.getState().instruments).toEqual([]);
    resolve(response(row)); await pending;
    fetchFn.mockRejectedValueOnce(new Error('duplicate destination'));
    await expect(useInstruments.getState().cloneInstrument(toFileInstrument(row), 'COPY')).rejects.toThrow('duplicate');
    expect(useInstruments.getState().instruments.map(item => item.symbol)).toEqual(['RECORDED']);
  });

  it('edits only the changed field without replacing legacy costs or hidden values', async () => {
    const fetchFn = setup().mockResolvedValue(response({ updated_count: 1, instruments: [{ ...row, default_spread: 3 }] }));
    const original = toFileInstrument(row);
    await useInstruments.getState().editInstrument(original, { ...original, spread: 3 });
    expect(JSON.parse(fetchFn.mock.calls[0][1].body)).toEqual({ instrument_ids: ['1'], updates: { default_spread: 3 } });
    expect(useInstruments.getState().instruments[0].record.commissions).toBe('4.75');
  });

  it('sends only enabled bulk fields and rejects mismatched confirmation IDs', async () => {
    const fetchFn = setup().mockResolvedValueOnce(response({ updated_count: 1, instruments: [{ ...row, margin_rate: .2 }] }))
      .mockResolvedValueOnce(response({ updated_count: 1, instruments: [{ ...row, id: '99' }] }));
    await useInstruments.getState().massEditInstruments(['1'], { fields: { marginRate: true }, value: { ...toFileInstrument(row), marginRate: .2, spread: 99 } });
    expect(JSON.parse(fetchFn.mock.calls[0][1].body)).toEqual({ instrument_ids: ['1'], updates: { margin_rate: .2 } });
    await expect(massEditRemoteInstruments(['1'], { margin_rate: .9 })).rejects.toThrow('different instrument');
  });

  it('ignores stale reads after session reset', async () => {
    let resolve!: (value: Response) => void;
    setup().mockReturnValueOnce(new Promise<Response>(done => { resolve = done; }));
    const pending = useInstruments.getState().refreshFromServer();
    useInstruments.getState().reset();
    resolve(response([row])); await pending;
    expect(useInstruments.getState().instruments).toEqual([]);
    expect(useInstruments.getState().loaded).toBe(false);
  });

  it('keeps a confirmed edit when an older read finishes later', async () => {
    let resolve!: (value: Response) => void;
    const fetchFn = setup().mockReturnValueOnce(new Promise<Response>(done => { resolve = done; }))
      .mockResolvedValueOnce(response({ updated_count: 1, instruments: [{ ...row, margin_rate: .25 }] }));
    const pending = useInstruments.getState().refreshFromServer();
    await useInstruments.getState().massEditInstruments(['1'], { fields: { marginRate: true }, value: { ...toFileInstrument(row), marginRate: .25 } });
    resolve(response([row])); await pending;
    expect(useInstruments.getState().instruments[0].marginRate).toBe(.25);
    expect(fetchFn).toHaveBeenCalledTimes(2);
  });

  it('rejects a nonfinite selected size before JSON can convert it to null', async () => {
    const fetchFn = setup();
    await expect(useInstruments.getState().massEditInstruments(['1'], { fields: { pipSize: true }, value: { ...toFileInstrument(row), pipSize: NaN } })).rejects.toThrow('valid instrument field');
    expect(fetchFn).not.toHaveBeenCalled();
  });

  it.each([null, {}, [{ ...row, contract_size: -1 }], [{ ...row, id: 1 }], [row, row]])('rejects malformed host catalog %j', async data => {
    setup().mockResolvedValue(response(data));
    await expect(fetchRemoteInstruments()).rejects.toThrow();
  });
});
