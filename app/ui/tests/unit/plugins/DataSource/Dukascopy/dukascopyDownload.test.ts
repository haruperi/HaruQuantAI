import { describe, expect, it } from 'vitest';
import { resolveDownloadModes, downloadStep, eligibleTargets, presetRange, validateDownload, mergeRanges, simulationSummary, type DownloadTarget } from '../../../../../app/plugins/DataSource/Dukascopy/dukascopyDownload';
const target: DownloadTarget = { id: 'd1', symbol: 'EURUSD', source: 'Dukascopy', timeframe: 'M1', from: '2010-01-01', to: '2020-01-01', bars: 10 };
describe('Dukascopy download rules', () => {
  it('filters mixed selection and rejects missing, cloned and active targets', () => {
    const request = { targets: [target], dateFrom: '2020-01-01', dateTo: '2020-02-01', dateType: 'custom' as const, overwrite: false, downloadType: 'standard' as const };
    expect(eligibleTargets([target, { ...target, id: 'other', source: 'File import' }], null)).toEqual([target]);
    expect(() => eligibleTargets([], null)).toThrow('at least one');
    expect(() => eligibleTargets([{ ...target, sourceDataId: 'clone' }], null)).toThrow('cloned');
    expect(() => eligibleTargets([target], { request, progress: 10, state: 'running' })).toThrow('in progress');
  });
  it('uses source preset behavior and clears only the selected bounds', () => {
    expect(presetRange('sinceLast', '2020-01-01', '2003-05-05', '', '2025-01-01', '2026-09-19')).toEqual({ from: '2020-01-01', to: '2025-01-01' });
    expect(presetRange('sixMonths', '', '2003-05-05', '', '2026-09-19', '2026-09-19').from).toBe('2026-03-19');
    expect(presetRange('allTime', '', '2003-05-05', '', '', '2026-09-19')).toEqual({ from: '2003-05-05', to: '2026-09-19' });
  });
  it('rejects invalid and reversed dates and future requests', () => {
    const request = { targets: [target], dateFrom: '2020-02-31', dateTo: '2020-03-01', dateType: 'custom' as const, overwrite: false, downloadType: 'cdn' as const };
    expect(() => validateDownload(request)).toThrow('valid date');
    expect(() => validateDownload({ ...request, dateFrom: '2020-04-01' })).toThrow('valid date');
    expect(() => validateDownload({ ...request, dateFrom: '2020-01-01', dateTo: '2999-01-01' })).toThrow('today');
  });
  it('deduplicates simulated coverage and preserves intervals outside overwrite', () => {
    const existing = [{ from: '2020-01-01', to: '2020-01-10' }];
    expect(mergeRanges(existing, { from: '2020-01-05', to: '2020-01-12' }, false)).toEqual([{ from: '2020-01-01', to: '2020-01-12' }]);
    expect(mergeRanges(existing, { from: '2020-01-05', to: '2020-01-07' }, true)).toEqual(existing);
    expect(simulationSummary(target, existing).bars).toBe(20);
    expect(existing).toEqual([{ from: '2020-01-01', to: '2020-01-10' }]);
  });
});

it('resolves each fast target independently and uses standard speed for unsupported targets', () => {
  for (const downloadType of ['cdn', 'cdn-cn'] as const) {
    const request = { targets: [target, { ...target, id: 'supported', fastDownloadAvailable: true }, { ...target, id: 'unsupported', fastDownloadAvailable: false }], dateFrom: '2020-01-01', dateTo: '2020-02-01', dateType: 'custom' as const, overwrite: false, downloadType };
    expect(resolveDownloadModes(request)).toEqual({ d1: 'standard', supported: downloadType, unsupported: 'standard' });
    expect(downloadStep({ request, state: 'running', progress: 0 })).toBe(5);
    const supported = { ...request, targets: [request.targets[1]] };
    expect(downloadStep({ request: supported, state: 'running', progress: 0 })).toBe(downloadType === 'cdn' ? 10 : 8);
    expect(resolveDownloadModes({ ...supported, downloadType: 'standard' })).toEqual({ supported: 'standard' });
  }
});
