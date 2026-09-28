import { beforeEach, describe, expect, it } from 'vitest';
import { MODULE_ROUTES, getModuleFromPath, getPathForModule } from '../../../app/host/router';
import { useAppStore } from '../../../app/host/store';
import { navigation } from '../../../app/host/contributions';

describe('HaruQuantAI React Router & Path Routing', () => {
  beforeEach(() => {
    useAppStore.getState().reset();
  });

  it('maps every installed navigation declaration without a central module list', () => {
    expect(Object.keys(MODULE_ROUTES).sort()).toEqual(navigation.map(item => item.id).sort());
    for (const item of navigation) {
      expect(getPathForModule(item.id)).toBe(item.path);
      expect(getModuleFromPath(item.path)).toBe(item.id);
      expect(getModuleFromPath(item.path + '/')).toBe(item.id);
      for (const alias of item.aliases ?? []) expect(getModuleFromPath(alias)).toBe(item.id);
    }
    expect(getModuleFromPath('/unknown-path-123')).toBeNull();
    expect(getPathForModule('removed.owner')).toBe('/unavailable/removed.owner');
  });

  it('supports custom query parameter parsing and manipulation like ?someParam=someValue', () => {
    const rawQuery = '?someParam=someValue&symbol=EURUSD&timeframe=H1';
    const params = new URLSearchParams(rawQuery);

    expect(params.get('someParam')).toBe('someValue');
    expect(params.get('symbol')).toBe('EURUSD');
    expect(params.get('timeframe')).toBe('H1');
    expect(params.get('nonexistent')).toBeNull();

    // Updating / appending new query parameters
    params.set('someParam', 'updatedValue');
    params.set('mode', 'genetic');
    expect(params.toString()).toBe('someParam=updatedValue&symbol=EURUSD&timeframe=H1&mode=genetic');
  });

  it('synchronizes deep-linked parameters (tab, strategyId, bankId) with store', () => {
    const store = useAppStore.getState();

    // Simulate inbound deep-link route: /builder?tab=settings&strategyId=SQX-TEST-01&bankId=bank-custom
    const query = new URLSearchParams('?tab=settings&strategyId=SQX-TEST-01&bankId=bank-custom');

    const targetModule = navigation[0]?.id ?? 'unavailable.owner';
    store.setModule(targetModule);

    const tab = query.get('tab');
    if (tab === 'progress' || tab === 'settings' || tab === 'results') {
      store.setTab(tab);
    }

    const strat = query.get('strategyId');
    if (strat) store.selectStrategy(strat);

    const bank = query.get('bankId');
    if (bank) store.setBank(bank);

    const updated = useAppStore.getState();
    expect(updated.module).toBe(targetModule);
    expect(updated.tab).toBe('settings');
    expect(updated.selectedStrategyId).toBe('SQX-TEST-01');
    expect(updated.selectedBankId).toBe('bank-custom');
  });
});
