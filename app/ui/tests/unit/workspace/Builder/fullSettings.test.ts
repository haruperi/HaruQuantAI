import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  additionalConfigRowIds,
  additionalConfigRowNames,
  blocksSections,
  buildingBlocksCatalog,
  crossChecksTabDefaults,
  crossChecksTabSectionTitles,
  describeAdditionalConfig,
  fitnessMethods,
  formatTimeOfDay,
  geneticOptionsDefaults,
  moneyManagementDefaults,
  nextTabLabel,
  oosPresets,
  oosRangePercents,
  prevTabLabel,
  settingsTabs,
  visibleSettingsTabs,
  tradingOptionsDefaults,
  whatToBuildDefaults,
} from '../../../../app/workspace/Builder/settings/settingsFixtures';

describe('Full settings fixtures (donor SQX144-EV-000038..043)', () => {
  it('registers the eleven eligible Build tabs in the donor strip order', () => {
    expect(settingsTabs.map(t => t.title)).toEqual([
      'What to build',
      'Parts to improve',
      'Genetic options',
      'Data',
      'Trading options',
      'Building blocks',
      'ATM',
      'Money management',
      'Cross checks (robustness)',
      'Ranking',
      'Notes',
    ]);
    for (const tab of settingsTabs) expect(tab.helpUrl).toMatch(/^https:\/\/strategyquant\.com\//);
  });

  it('applies the donor prev/next label rules with first/last hidden', () => {
    expect(prevTabLabel(0)).toBeNull();
    expect(nextTabLabel(settingsTabs.length - 1)).toBeNull();
    expect(prevTabLabel(1)).toBe('< What to build');
    expect(nextTabLabel(1)).toBe('Genetic options >');
    expect(nextTabLabel(settingsTabs.length - 2)).toBe('Notes >');
  });

  it('orders the six additional build config rows and names them per donor', () => {
    expect(additionalConfigRowIds).toEqual(['tradingDirections', 'strategyStyle', 'buildMode', 'conditions', 'stopLoss', 'profitTarget']);
    expect(additionalConfigRowNames.buildMode).toBe('Build mode');
    expect(additionalConfigRowNames.conditions).toBe('# of Conditions, Periods');
  });

  it('describes the default config with the donor string shapes', () => {
    expect(describeAdditionalConfig(whatToBuildDefaults, 'tradingDirections')).toBe('Both (Long & Short), Entry symmetry, Exit symmetry');
    expect(describeAdditionalConfig(whatToBuildDefaults, 'strategyStyle')).toBe('SQX Signals');
    expect(describeAdditionalConfig(whatToBuildDefaults, 'buildMode')).toBe('Genetic evolution, 100 generations max. / 4 islands / 100 per island, Restart on finish');
    expect(describeAdditionalConfig(whatToBuildDefaults, 'stopLoss')).toBe('Required, Pips based: 20-120 pips');
    expect(describeAdditionalConfig(whatToBuildDefaults, 'conditions')).toContain('Conditions to generate: 1-12');
  });

  it('drops symmetry from the trading directions description when both are off', () => {
    const state = {
      ...whatToBuildDefaults,
      tradingDirections: { type: 'both' as const, entrySymmetry: false, exitSymmetry: false },
    };
    expect(describeAdditionalConfig(state, 'tradingDirections')).toBe('Both (Long & Short), No symmetry');
  });

  it('carries the installed template genetic defaults', () => {
    expect(geneticOptionsDefaults).toMatchObject({
      maxGenerations: 100,
      populationSize: 100,
      islands: 4,
      crossoverProbability: 93,
      mutationProbability: 30,
      migrationModulo: 87,
      migrationRate: 6,
    });
  });

  it('offers the five donor most-used OOS presets and computes part percents', () => {
    expect(oosPresets).toHaveLength(5);
    expect(oosPresets[0].title).toBe('IST: 50, ISV: 20, OOS: 30');
    const percents = oosRangePercents([
      { type: 'IST', from: '2026.01.01', to: '2026.01.11' },
      { type: 'ISV', from: '2026.01.11', to: '2026.01.21' },
    ]);
    expect(percents).toEqual([50, 50]);
  });

  it('formats time-of-day properties as HH:MM', () => {
    expect(formatTimeOfDay(82800)).toBe('23:00');
    expect(formatTimeOfDay(32400)).toBe('09:00');
  });

  it('lists the trading options with the template defaults', () => {
    const keys = tradingOptionsDefaults.map(p => p.key);
    expect(keys).toContain('ExitOnFriday');
    expect(keys).toContain('LimitTimeRange');
    expect(tradingOptionsDefaults.find(p => p.key === 'MaxTradesPerDay')?.value).toBe(1);
  });

  it('ships the money management methods with FixedSize active', () => {
    const active = moneyManagementDefaults.methods.filter(m => m.use);
    expect(active.map(m => m.key)).toEqual(['FixedSize']);
    expect(moneyManagementDefaults.initialCapital).toBe(10000);
    expect(moneyManagementDefaults.methods).toHaveLength(5);
  });

  it('groups the building blocks catalog by donor sections', () => {
    for (const section of blocksSections) {
      const entries = buildingBlocksCatalog.filter(b => b.category === section.category);
      expect(entries.length).toBeGreaterThan(0);
    }
    expect(buildingBlocksCatalog.filter(b => b.category === 'indicators').length).toBeGreaterThanOrEqual(50);
    expect(buildingBlocksCatalog.filter(b => b.category === 'orderTypes')).toContainEqual(expect.objectContaining({ key: 'EnterAtMarket' }));
  });

  it('spreads the nine cross checks across the three speed sections', () => {
    expect(crossChecksTabSectionTitles.map(s => s.title)).toEqual(['Basic (fast)', 'Standard (slow)', 'Extensive (slowest)']);
    const counts = [0, 1, 2].map(section => crossChecksTabDefaults.filter(c => c.section === section).length);
    expect(counts).toEqual([3, 3, 3]);
    expect(crossChecksTabDefaults.find(c => c.id === 'higher-precision')?.use).toBe(true);
  });

  it('offers the fitness method list with the default Return/DD criterion', () => {
    expect(fitnessMethods.map(m => m.value)).toContain('ComputeFromStrategyResult');
    expect(fitnessMethods.map(m => m.value)).toContain('ReturnDDRatio');
  });
});

 describe('Builder settings visibility', () => {
  it('only includes Parts to improve in improve mode and excludes Custom analysis', () => {
    for (const type of ['simple', 'multiTf', 'template'] as const) {
      const tabs = visibleSettingsTabs(type);
      expect(tabs).toHaveLength(10);
      expect(tabs.some(t => t.id === 'parts-to-improve' || t.id === 'custom-analysis')).toBe(false);
      expect(nextTabLabel(0, tabs)).toBe('Genetic options >');
    }
    expect(visibleSettingsTabs('improve')).toHaveLength(11);
    expect(nextTabLabel(0, visibleSettingsTabs('improve'))).toBe('Parts to improve >');
  });
});

describe('saved Builder settings hydration', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('fills fields absent from an older Builder record without replacing saved values', async () => {
    vi.resetModules();
    const memory = new Map<string, string>([
      [
        'sqx-recreation-v1',
        JSON.stringify({
          state: { module: 'builder', tab: 'settings', builder: { population: 250 } },
          version: 1,
        }),
      ],
    ]);
    const storage = {
      getItem: (key: string) => memory.get(key) ?? null,
      setItem: (key: string, value: string) => memory.set(key, value),
      removeItem: (key: string) => memory.delete(key),
    };
    vi.stubGlobal('window', { localStorage: storage });
    vi.stubGlobal('localStorage', storage);

    const { useAppStore } = await import('../../../../app/workspace/Builder/localState');
    await useAppStore.persist.rehydrate();
    const { builder } = useAppStore.getState();

    expect(builder.population).toBe(250);
    expect(builder.customBlocks).toEqual({});
    expect(builder.crossChecks.length).toBeGreaterThan(0);
    expect(builder.mode).toBe('Genetic evolution');
  });
});
