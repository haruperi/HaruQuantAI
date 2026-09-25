import { describe, expect, it } from 'vitest';
import {
  ENGINE_CHART_TYPES,
  bestStrategies,
  buildOptionRows,
  crossCheckCategories,
  databankFitnessSeries,
  dataSettingsFixture,
  displayCrossCheckTitle,
  idleProgressStats,
  predefinedConfigs,
  resultRankTitle,
  runFrameAt,
  toggleCrossCheck,
} from '../../../../src/workspace/Builder/fixtures';

describe('Progress tab fixtures (donor SQX144-EV-000032..037)', () => {
  it('keeps the idle stats snapshot at the donor idle values', () => {
    expect(idleProgressStats).toEqual({
      strategiesGenerated: 0,
      timePerStrategy: '0 ms.',
      timePerAcceptedStrategy: '0 ms.',
      rejected: '0 / 0.00 %',
      accepted: '0 / 0.00 %',
      strategiesPerHour: '0.00',
      acceptedPerHour: '0.00',
      runningTime: '0 ms.',
      inDatabank: 0,
    });
  });

  it('produces deterministic, monotonically growing run frames', () => {
    const a = runFrameAt(3);
    const b = runFrameAt(3);
    expect(a).toEqual(b);
    expect(a.stats.strategiesGenerated).toBe(36);
    expect(runFrameAt(4).stats.strategiesGenerated).toBeGreaterThan(a.stats.strategiesGenerated);
    expect(a.logLine).toBeTruthy();
    expect(runFrameAt(0).logLine).toBe('Project started');
  });

  it('formats rejection/acceptance with the donor "n / pct %" shape', () => {
    const frame = runFrameAt(2);
    const [rejectedCount] = frame.stats.rejected.split(' / ');
    const [acceptedCount] = frame.stats.accepted.split(' / ');
    expect(Number(rejectedCount) + Number(acceptedCount)).toBe(frame.stats.strategiesGenerated);
    expect(frame.stats.rejected).toMatch(/ %$/);
    expect(frame.stats.accepted).toMatch(/ %$/);
  });

  it('exposes exactly the two donor-observed engine chart types', () => {
    expect([...ENGINE_CHART_TYPES]).toEqual(['Databank Fitness - IS Training', 'Heap memory chart']);
  });

  it('ships the donor fitness chart legend in donor order', () => {
    expect(databankFitnessSeries.map(s => s.name)).toEqual(['Top Strategy', 'Top 10 Avg', 'All Avg']);
  });

  it('lists the eight predefined config entries with tooltips', () => {
    expect(predefinedConfigs.map(c => c.label)).toEqual([
      'Default (forex)',
      'Default (futures)',
      'Default (stockpicker)',
      'Market',
      'Trend following',
      'Mean reversal',
      'Fuzzy',
      'Daily',
    ]);
    for (const config of predefinedConfigs) expect(config.info.length).toBeGreaterThan(0);
  });

  it('renders the Build options rows in donor order with values', () => {
    expect(buildOptionRows.map(r => r.name)).toEqual([
      'What to build',
      'Building blocks',
      'Trading options',
      'Money Management',
    ]);
    expect(buildOptionRows[0].lines[0]).toBe('Simple strategies, SL&PT required, fixed pips');
  });

  it('keeps the data settings demo snapshot coherent', () => {
    expect(dataSettingsFixture.engines).toContain(dataSettingsFixture.engine);
    expect(dataSettingsFixture.timeframe).toBe('D1');
    expect(dataSettingsFixture.oosLabel).toBe('OOS: N/A');
  });

  it('organizes the nine cross checks into FAST / SLOW / VERY SLOW', () => {
    expect(crossCheckCategories.map(c => c.name)).toEqual(['FAST', 'SLOW', 'VERY SLOW']);
    const total = crossCheckCategories.reduce((n, c) => n + c.items.length, 0);
    expect(total).toBe(9);
    // Default config: only "Retest with higher precision" is on (observed).
    const on = crossCheckCategories.flatMap(c => c.items).filter(i => i.use);
    expect(on.map(i => i.title)).toEqual(['Retest with higher precision']);
  });

  it('truncates cross-check titles at 32 characters plus a period', () => {
    expect(displayCrossCheckTitle('Opt. Profile / Sys. Param. Permutation')).toBe('Opt. Profile / Sys. Param. Permu.');
    expect(displayCrossCheckTitle('Walk-Forward Matrix')).toBe('Walk-Forward Matrix');
  });

  it('toggles one cross check at a time and respects Disable all', () => {
    const toggled = toggleCrossCheck(crossCheckCategories, 'what-if', false);
    const item = toggled.flatMap(c => c.items).find(i => i.id === 'what-if');
    expect(item?.use).toBe(true);
    const blocked = toggleCrossCheck(crossCheckCategories, 'what-if', true);
    expect(blocked.flatMap(c => c.items).find(i => i.id === 'what-if')?.use).toBe(false);
  });

  it('renders the donor ranking titles for the result cards', () => {
    expect(resultRankTitle(0, 'Strategy 023')).toBe('Best strategy so far: Strategy 023');
    expect(resultRankTitle(1, 'Strategy 007')).toBe('2nd Best strategy so far: Strategy 007');
    expect(resultRankTitle(2, 'Strategy 041')).toBe('3rd Best strategy so far: Strategy 041');
    expect(resultRankTitle(0, null)).toBe('No results so far');
  });

  it('provides three demo best strategies with overview and equity data', () => {
    expect(bestStrategies).toHaveLength(3);
    for (const strategy of bestStrategies) {
      expect(strategy.overview.length).toBeGreaterThan(0);
      expect(strategy.equity.length).toBeGreaterThan(10);
    }
  });
});
