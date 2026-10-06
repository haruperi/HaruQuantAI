import { describe, expect, it } from 'vitest';
import {
  benchmarkNormalizations,
  builtInResultTabs,
  customAnalysisActions,
  defaultCustomAnalysisTabs,
  directionOptions,
  hiddenUntilResultTabs,
  NO_RESULT_CHOSEN,
  orderResultTabs,
  overviewTemplates,
  sampleListIn,
  sampleListOut,
  sourceCodeDescriptions,
  sourceCodeGenerators,
  sourceCodeParamsDefaults,
  tradeListViews,
} from '../../../../app/workspace/Builder/results/resultsFixtures';

describe('Results tab fixtures (donor retained target UI; current donor equivalence unverified)', () => {
  it('registers the visible built-in tabs in the donor strip order', () => {
    expect(builtInResultTabs.map(t => t.title)).toEqual([
      'Overview',
      'SP overview',
      'List of trades',
      'Equity chart',
      'Trade analysis',
      'Profile chart',
      'Strategy config',
      'Source Code',
    ]);
  });

  it('keeps result-only tabs hidden while no result is chosen', () => {
    expect(hiddenUntilResultTabs.map(t => t.title)).toContain('Monte Carlo tests');
    const visible = builtInResultTabs.map(t => t.id);
    for (const hidden of hiddenUntilResultTabs) {
      expect(visible).not.toContain(hidden.id);
    }
  });

  it('sorts custom analysis tabs after the built-ins', () => {
    const ordered = orderResultTabs(builtInResultTabs, defaultCustomAnalysisTabs);
    expect(ordered.map(t => t.title)).toEqual([
      ...builtInResultTabs.map(t => t.title),
      'Prop Monte Carlo',
      'Prop analytics',
    ]);
    expect(ordered[ordered.length - 2].isCustom).toBe(true);
    expect(ordered[ordered.length - 1].isCustom).toBe(true);
  });

  it('keeps custom tabs stable for new analyses added later', () => {
    const ordered = orderResultTabs(builtInResultTabs, [
      ...defaultCustomAnalysisTabs,
      'My Analysis',
    ]);
    expect(ordered[ordered.length - 1].title).toBe('My Analysis');
    expect(ordered[ordered.length - 1].id).toBe('custom:My Analysis');
  });

  it('uses the donor info line text', () => {
    expect(NO_RESULT_CHOSEN).toBe(
      'No result chosen - Double-click on result on databank to see the details',
    );
  });

  it('labels the direction segmented buttons L+S / Lng / Shr', () => {
    expect(directionOptions.map(d => d.label)).toEqual(['L+S', 'Lng', 'Shr']);
  });

  it('splits sample dropdown fixtures into IS and OOS groups', () => {
    for (const item of sampleListIn) expect(item.startsWith('IS')).toBe(true);
    for (const item of sampleListOut) expect(item.startsWith('OOS')).toBe(true);
  });

  it('defaults the overview template select to SQ Default', () => {
    expect(overviewTemplates).toEqual([{ value: 'SQDefault', label: 'SQ Default' }]);
  });

  it('ships the tradelist default view', () => {
    expect(tradeListViews).toEqual([{ value: 'Default', label: 'Default' }]);
  });

  it('lists source code generators with the pseudo-code default first', () => {
    expect(sourceCodeGenerators[0]).toBe('Pseudo Code(*.TXT)');
    expect(sourceCodeGenerators).toContain('Expert Advisor for MetaTrader4 (*.MQ4)');
    for (const gen of sourceCodeGenerators) {
      expect(sourceCodeDescriptions[gen]).toBeTruthy();
    }
  });

  it('defaults parameter variables to recommended parameters', () => {
    expect(sourceCodeParamsDefaults.parametrizeType).toBe(0);
    expect(sourceCodeParamsDefaults.symmetricVariables).toBe(true);
  });

  it('uses the donor benchmark normalization option labels', () => {
    expect(benchmarkNormalizations.map(n => n.label)).toEqual([
      'off',
      'normalize by $ drawdown',
      'normalize by % drawdown',
      'normalize by money management',
      'normalize by exposure',
    ]);
  });

  it('orders the custom tab menu actions Rename before Delete', () => {
    expect([...customAnalysisActions].sort((a, b) => a.position - b.position).map(a => a.title)).toEqual([
      'Rename',
      'Delete',
    ]);
  });
});
