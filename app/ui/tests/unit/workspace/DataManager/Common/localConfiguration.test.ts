import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { effectiveInstruments, newInstrument } from '../../../../../app/workspace/DataManager/Catalogs/Instruments/fileSymbols';
import { effectiveSessions, type SessionDefinition } from '../../../../../app/workspace/DataManager/Catalogs/Sessions/sessions';

import { brokerClockPort } from '../../../../../app/workspace/DataManager/Common/catalogClient';
const clockPost = vi.hoisted(() => vi.fn());
vi.mock('../../../../../app/host/transport', () => ({ createDomainClient: () => ({ post: clockPost }) }));

const persisted = vi.hoisted(() => ({ states: new Map<string, any>(), fail: false, writes: vi.fn() }));
vi.mock('../../../../../app/workspace/DataManager/Common/catalogClient', async importOriginal => ({
  ...await importOriginal<typeof import('../../../../../app/workspace/DataManager/Common/catalogClient')>(),
  catalogPort: (kind: string) => ({
    read: async () => structuredClone(persisted.states.get(kind) ?? (kind === 'instruments' ? { instruments: [], overrides: {}, removed: [] } : kind === 'sessions' ? { sessions: [], overrides: {}, removed: [] } : { [kind]: [] })),
    write: async (state: object) => { if (persisted.fail) throw new Error('Backend unavailable'); persisted.writes(kind, state); persisted.states.set(kind, structuredClone(state)); return structuredClone(state); },
  }),
}));
const instrument = { ...newInstrument(), symbol: 'CUSTOM', name: 'My instrument' };
const session: SessionDefinition = {
  name: 'MySession', broker: '-1', brokerName: 'Default',
  elements: [{ dayFrom: 'Mon', dayTo: 'Mon', timeFrom: '08:00', timeTo: '17:00', eod: true }],
};

describe('local configuration without runtime seed data', () => {
  let saved: Map<string, string>;
  beforeEach(() => {
    vi.resetModules();
    saved = new Map(); persisted.states.clear(); persisted.fail = false; persisted.writes.mockClear();
    vi.stubGlobal('localStorage', {
      getItem: (key: string) => saved.get(key) ?? null,
      setItem: (key: string, value: string) => saved.set(key, value),
    });
  });
  afterEach(() => vi.unstubAllGlobals());

  it('starts catalogs empty and retains explicit customizations of former seed records', () => {
    expect(effectiveInstruments([])).toEqual([]);
    expect(effectiveSessions([], {}, [])).toEqual([]);
    expect(effectiveInstruments([], { CUSTOM: instrument })).toEqual([instrument]);
    expect(effectiveSessions([], { MySession: session }, [])).toEqual([session]);
    expect(effectiveInstruments([], { CUSTOM: instrument }, ['CUSTOM'])).toEqual([]);
    expect(effectiveSessions([], { MySession: session }, ['MySession'])).toEqual([]);
  });

  it('ignores legacy dataset jobs while preserving broker configuration and storage', async () => {
    const key = 'sqx-data-manager-v1';
    const broker = { id: 'b1', name: '[Mine]', postfix: '_mine', timezone: 'UTC', mtUse: true, instruments: [], stocks: [] };
    const legacy = JSON.stringify({ version: 2, brokers: [broker], definitions: [{ symbol: 'AUDCAD' }], brokerJob: { state: 'running' } });
    saved.set(key, legacy);
    const { useDataManagerStore } = await import('../../../../../app/workspace/DataManager/Common/dataManagerStore');
    expect(useDataManagerStore.getState().brokers).toEqual([]);
    await useDataManagerStore.getState().importLegacy();
    expect(useDataManagerStore.getState().brokers[0].id).toBe('b1');
    expect(useDataManagerStore.getState()).not.toHaveProperty('definitions');
    expect(useDataManagerStore.getState()).not.toHaveProperty('brokerJob');
    expect(saved.get(key)).toBe(legacy);
    await useDataManagerStore.getState().saveBrokerStocks('b1', ['REAL']);
    expect(persisted.states.get('brokers').brokers[0].stocks).toEqual(['REAL']);
    expect(JSON.parse(saved.get(key)!).definitions).toEqual([{ symbol: 'AUDCAD' }]);
  });

  it('preserves custom instruments and legacy file definitions without exposing them as datasets', async () => {
    const key = 'sqx-file-symbols-v1';
    const legacy = JSON.stringify({ version: 3, instruments: [], overrides: { CUSTOM: instrument }, removed: [], definitions: [{ symbol: 'OLD_FILE' }] });
    saved.set(key, legacy);
    const { useFileSymbols } = await import('../../../../../app/workspace/DataManager/Catalogs/Instruments/fileSymbolsStore');
    expect(useFileSymbols.getState().storageError).toBe('');
    expect(useFileSymbols.getState()).not.toHaveProperty('definitions');
    expect(saved.get(key)).toBe(legacy);
    await useFileSymbols.getState().importLegacy();
    await useFileSymbols.getState().editInstrument('CUSTOM', { ...instrument, name: 'Edited' }, ['-1']);
    expect(JSON.parse(saved.get(key)!).definitions).toEqual([{ symbol: 'OLD_FILE' }]);
    vi.resetModules();
    const reloaded = await import('../../../../../app/workspace/DataManager/Catalogs/Instruments/fileSymbolsStore');
    await reloaded.useFileSymbols.getState().refresh();
    expect(reloaded.useFileSymbols.getState().overrides.CUSTOM.name).toBe('Edited');
  });

  it('retains saved session overrides and does not inject the old catalog', async () => {
    const key = 'haru-data-sessions-v1';
    const legacy = JSON.stringify({ version: 1, sessions: [], overrides: { MySession: session }, removed: [] });
    saved.set(key, legacy);
    const { useSessions } = await import('../../../../../app/workspace/DataManager/Catalogs/Sessions/sessionStore');
    expect(useSessions.getState().storageError).toBe('');
    expect(saved.get(key)).toBe(legacy);
    await useSessions.getState().importLegacy();
    await useSessions.getState().edit('MySession', session, ['-1']);
    expect(effectiveSessions(useSessions.getState().sessions, useSessions.getState().overrides, [])).toEqual([session]);
  });

  it('ignores generated stock-group data and jobs while retaining the group', async () => {
    const key = 'sqx-stock-groups-v1';
    const group = { id: 'g1', name: '[Mine]', description: '', system: false, members: [{ ticker: 'AAPL' }] };
    const legacy = JSON.stringify({ version: 1, groups: [group], generated: [{ symbol: 'AAPL', bars: 999 }], job: { state: 'running' } });
    saved.set(key, legacy);
    const { useStockGroups } = await import('../../../../../app/workspace/DataManager/Catalogs/StockGroups/stockGroupsStore');
    expect(useStockGroups.getState().groups).toEqual([]);
    await useStockGroups.getState().importLegacy();
    expect(useStockGroups.getState().groups).toEqual([group]);
    expect(useStockGroups.getState()).not.toHaveProperty('generated');
    expect(useStockGroups.getState()).not.toHaveProperty('job');
    expect(saved.get(key)).toBe(legacy);
    await useStockGroups.getState().replaceMembers('g1', [{ ticker: 'MSFT' }]);
    expect(JSON.parse(saved.get(key)!).generated).toEqual([{ symbol: 'AAPL', bars: 999 }]);
  });
});

it('does not report an instrument mutation as saved when backend persistence fails', async () => {
  vi.resetModules(); vi.stubGlobal('localStorage', { getItem: () => null }); persisted.states.clear(); persisted.fail = true;
  const { useFileSymbols } = await import('../../../../../app/workspace/DataManager/Catalogs/Instruments/fileSymbolsStore');
  await expect(useFileSymbols.getState().addInstrument(instrument, ['-1'])).rejects.toThrow('Backend unavailable');
  expect(useFileSymbols.getState().instruments).toEqual([]); persisted.fail = false; vi.unstubAllGlobals();
});

describe('broker clock metadata port', () => {
  beforeEach(() => clockPost.mockReset());
  it('reads authoritative database policy rather than browser clock configuration', async () => {
    const response = { revision: 0, revisions: [], database_broker_id: '6', schema: { properties: {} } };
    clockPost.mockResolvedValueOnce(response);
    expect(await brokerClockPort.read('profile')).toEqual(response);
    expect(clockPost).toHaveBeenCalledWith('/broker_clock.get', { broker_id: 'profile' });
  });
  it('sends an explicit optimistic revision and leaves policy validation to the host', async () => {
    const policy = { revision: 4, standard_offset_minutes: 120, dst_rule: 'us' };
    clockPost.mockResolvedValueOnce({ revision: 4, revisions: [policy] });
    await brokerClockPort.write('profile', 3, policy);
    expect(clockPost).toHaveBeenCalledWith('/broker_clock.replace', { broker_id: 'profile', expected_revision: 3, policy });
  });
});
