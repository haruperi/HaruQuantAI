import { describe, expect, it } from 'vitest';
import {
  PORTFOLIO_MENU,
  SAVE_MENU,
  TOOLS_MENU,
  TOOLBAR_BUTTON_ORDER,
} from '../../../../../app/plugins/databank/Builder/ProjectDatabanks/DatabankToolbar';
import { DEFAULT_VIEW_PRESETS } from '../../../../../app/plugins/databank/Builder/ProjectDatabanks/databankColumns';
import { strategyPassesMockChecks } from '../../../../../app/plugins/databank/Builder/ProjectDatabanks/DatabankPanel';

describe('Databanks toolbar inventory (donor SQX144-EV-000028)', () => {
  it('orders toolbar buttons exactly as the donor plugin positions', () => {
    expect(TOOLBAR_BUTTON_ORDER.map(b => b.label)).toEqual([
      'Load',
      'Save',
      'Delete',
      'Clear all',
      'Retest',
      'Rename',
      'Filter by correlation',
      'Portfolio',
      'Tools',
    ]);
  });

  it('styles Delete and Clear all as destructive', () => {
    const destructive = TOOLBAR_BUTTON_ORDER.filter(b => b.destructive).map(b => b.label);
    expect(destructive).toEqual(['Delete', 'Clear all']);
  });

  it('lists the donor Save menu options in order', () => {
    expect(SAVE_MENU).toEqual([
      'Save to SQ X format',
      'HTML report',
      'PDF report',
      'Source code',
      'Export databank contents',
      'Save stats in SQ3 format',
      'Export strategy trades to CSV/XLSX',
    ]);
  });

  it('lists the donor Portfolio menu options in order', () => {
    expect(PORTFOLIO_MENU).toEqual([
      'Merge strategies',
      'Split strategies',
      'Merge WF results',
      'Move to Portfolio Composer',
      'Move to Portfolio Master',
    ]);
  });

  it('builds the Tools menu with nested Edit and Select submenus', () => {
    expect(TOOLS_MENU).toEqual([
      { label: 'Edit', children: ['Parameters', 'Strategy'] },
      { label: 'Select', children: ['Passed', 'Failed'] },
      { label: 'Set note' },
      { label: 'Compare' },
      { label: 'Run CA' },
    ]);
  });
});

describe('Databanks default grid view (donor SQX144-EV-000031)', () => {
  it('names the default view as the donor does', () => {
    expect(DEFAULT_VIEW_PRESETS[0].name).toBe('Default - Main data');
  });

  it('pins Strategy Name first and follows the donor column order', () => {
    const ids = DEFAULT_VIEW_PRESETS[0].columns.map(c => c.columnId);
    expect(ids[0]).toBe('name');
    expect(ids.slice(1, 8)).toEqual([
      'fitness',
      'symbol',
      'timeframe',
      'netProfit',
      'miniEquity',
      'trades',
      'profitFactor',
    ]);
  });
});

describe('Tools > Select mock cross-check rule', () => {
  it('passes profitable, sufficiently traded, low-drawdown strategies', () => {
    expect(strategyPassesMockChecks(12000, 120, 9000)).toBe(true);
  });

  it('rejects unprofitable, thin, or high-drawdown strategies', () => {
    expect(strategyPassesMockChecks(-500, 120, 9000)).toBe(false);
    expect(strategyPassesMockChecks(12000, 40, 9000)).toBe(false);
    expect(strategyPassesMockChecks(12000, 120, 40000)).toBe(false);
  });
});
