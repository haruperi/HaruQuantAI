import { beforeEach, describe, expect, it } from 'vitest';
import { MODULE_ROUTES, getModuleFromPath, getPathForModule } from '../../../app/host/router';
import { useAppStore } from '../../../app/host/store';
import type { ModuleId } from '../../../app/host/types';

describe('HaruQuantAI React Router & Path Routing', () => {
  beforeEach(() => {
    useAppStore.getState().reset();
  });

  it('maps all 18 workspaces and utility modules to canonical URL paths', () => {
    const expectedModules: ModuleId[] = [
      'home',
      'datamanager',
      'chart',
      'business',
      'builder',
      'algowizard',
      'codeeditor',
      'neuralnet',
      'retester',
      'optimizer',
      'mtanalyzer',
      'projects',
      'portfolio',
      'composer',
      'trading',
      'debugconsole',
      'gridcontrol',
      'gridtest',
    ];

    expectedModules.forEach((mod) => {
      expect(MODULE_ROUTES[mod]).toBeDefined();
      expect(typeof MODULE_ROUTES[mod]).toBe('string');
      expect(getPathForModule(mod)).toBe(MODULE_ROUTES[mod]);
    });

    expect(MODULE_ROUTES.home).toBe('/');
    expect(MODULE_ROUTES.datamanager).toBe('/datamanager');
    expect(getPathForModule('chart')).toBe('/chart');
    expect(MODULE_ROUTES.builder).toBe('/builder');
    expect(MODULE_ROUTES.codeeditor).toBe('/codeeditor');
    expect(MODULE_ROUTES.business).toBe('/business');
    expect(MODULE_ROUTES.projects).toBe('/projects');
  });

  it('resolves URL paths to corresponding ModuleId accurately', () => {
    expect(getModuleFromPath('/')).toBe('home');
    expect(getModuleFromPath('/home')).toBe('home');
    expect(getModuleFromPath('/datamanager')).toBe('datamanager');
    expect(getModuleFromPath('/datamanager/')).toBe('datamanager');
    expect(getModuleFromPath('/chart')).toBe('chart');
    expect(getModuleFromPath('/chart/')).toBe('chart');
    expect(getModuleFromPath('/builder')).toBe('builder');
    expect(getModuleFromPath('/portfolio')).toBe('portfolio');
    expect(getModuleFromPath('/codeeditor')).toBe('codeeditor');
    expect(getModuleFromPath('/business')).toBe('business');
    expect(getModuleFromPath('/projects')).toBe('projects');
    expect(getModuleFromPath('/debugconsole')).toBe('debugconsole');
    expect(getModuleFromPath('/gridcontrol')).toBe('gridcontrol');
    expect(getModuleFromPath('/gridtest')).toBe('gridtest');

    // Unknown or invalid routes return null
    expect(getModuleFromPath('/unknown-path-123')).toBeNull();
    expect(getModuleFromPath('/invalid')).toBeNull();
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

    const targetModule = getModuleFromPath('/builder');
    expect(targetModule).toBe('builder');
    if (targetModule) store.setModule(targetModule);

    const tab = query.get('tab');
    if (tab === 'progress' || tab === 'settings' || tab === 'results') {
      store.setTab(tab);
    }

    const strat = query.get('strategyId');
    if (strat) store.selectStrategy(strat);

    const bank = query.get('bankId');
    if (bank) store.setBank(bank);

    const updated = useAppStore.getState();
    expect(updated.module).toBe('builder');
    expect(updated.tab).toBe('settings');
    expect(updated.selectedStrategyId).toBe('SQX-TEST-01');
    expect(updated.selectedBankId).toBe('bank-custom');
  });
});
