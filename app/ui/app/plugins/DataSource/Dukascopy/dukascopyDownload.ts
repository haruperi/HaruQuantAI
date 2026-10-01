import { catalogue } from './dukascopy';
export type DownloadMode = 'standard' | 'cdn' | 'cdn-cn';
export type Preset = 'sinceLast' | 'sixMonths' | 'year' | 'fiveYears' | 'tenYears' | 'allTime' | 'custom';
export interface DownloadTarget { id: string; symbol: string; source: string; underlying?: string; instrument?: string; timeframe: string; from: string; to: string; bars: number; sourceDataId?: string; fastDownloadAvailable?: boolean }
export interface DownloadRequest { targets: DownloadTarget[]; dateFrom: string; dateTo: string; dateType: Preset; overwrite: boolean; downloadType: DownloadMode }
export interface Interval { from: string; to: string }
export interface DownloadJob { request: DownloadRequest; state: 'running' | 'paused' | 'cancelled' | 'completed' | 'failed'; progress: number; error?: string; resolvedModes?: Record<string, DownloadMode>; jobId?: string; canPause?: boolean; outcome?: 'complete' | 'partial' | 'empty' }
export interface DownloadState { job: DownloadJob | null; ranges: Record<string, Interval[]>; preferred: DownloadMode | null }
export const emptyDownload: DownloadState = { job: null, ranges: {}, preferred: null };
export function today(): string { const now = new Date(); return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`; }
export function validDate(value: string): boolean { return /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value; }
export function availableStart(target: DownloadTarget, precision = false): string {
  const item = catalogue.find(row => row.symbol === (target.underlying ?? target.instrument ?? target.symbol));
  return item ? (precision && target.timeframe.startsWith('M1') ? item.dateFromM1 : item.dateFrom) : today();
}
export function eligibleTargets(targets: DownloadTarget[], job: DownloadJob | null): DownloadTarget[] {
  const eligible = targets.filter(row => row.source === 'Dukascopy');
  if (!eligible.length) throw new Error('You must select at least one Dukascopy record.');
  if (eligible.some(row => row.sourceDataId)) throw new Error('You cannot download to cloned data.');
  const available = eligible.filter(row => !job || !['running', 'paused'].includes(job.state) || !job.request.targets.some(active => active.id === row.id));
  if (!available.length) throw new Error('Cannot start another action on data in progress.');
  return available;
}
export function presetRange(preset: Preset, last: string, minimum: string, from: string, to: string, now = today()): Interval {
  if (preset === 'custom') return { from, to };
  if (preset === 'allTime') return { from: minimum, to: now };
  if (preset === 'sinceLast') return { from: last, to };
  const date = new Date(`${now}T12:00:00Z`);
  if (preset === 'sixMonths') date.setUTCMonth(date.getUTCMonth() - 6);
  else date.setUTCFullYear(date.getUTCFullYear() - ({ year: 1, fiveYears: 5, tenYears: 10 }[preset]));
  return { from: [minimum, date.toISOString().slice(0, 10)].sort().at(-1)!, to };
}
export function validateDownload(request: DownloadRequest, now = today()): void {
  if (!request.targets.length || request.targets.some(row => row.source !== 'Dukascopy' || row.sourceDataId)) throw new Error('Select eligible Dukascopy records.');
  if (!['standard', 'cdn', 'cdn-cn'].includes(request.downloadType)) throw new Error('Choose a download mode.');
  if (!validDate(request.dateFrom) || !validDate(request.dateTo) || request.dateFrom > request.dateTo) throw new Error('Choose a valid date range with From on or before To.');
  if (request.dateFrom < availableStart(request.targets[0]) || request.dateTo > now) throw new Error('Dates must be within the available range and today.');
  if (request.targets.some(row => request.dateTo < availableStart(row, true))) throw new Error('The selected range is before data availability for a selected symbol.');
}
/** Track only simulated intervals; imported seed counts remain separate and untouched. */
export function mergeRanges(existing: Interval[], incoming: Interval, overwrite: boolean): Interval[] {
  const day = (iso: string, offset: number) => new Date(Date.parse(iso) + offset * 86400000).toISOString().slice(0, 10);
  const retained = overwrite ? existing.flatMap(row => row.to < incoming.from || row.from > incoming.to ? [row] : [
    ...(row.from < incoming.from ? [{ from: row.from, to: day(incoming.from, -1) }] : []),
    ...(row.to > incoming.to ? [{ from: day(incoming.to, 1), to: row.to }] : []),
  ]) : existing;
  const result: Interval[] = [];
  for (const range of [...retained, incoming].sort((a, b) => a.from.localeCompare(b.from))) {
    const previous = result.at(-1);
    if (previous && Date.parse(range.from) <= Date.parse(previous.to) + 86400000) previous.to = previous.to > range.to ? previous.to : range.to;
    else result.push({ ...range });
  }
  return result;
}
export function simulationSummary(target: DownloadTarget, ranges: Interval[]) {
  if (!ranges.length) return { from: target.from, to: target.to, bars: target.bars };
  // Deterministic metadata only: one synthetic sample per simulated calendar day.
  const samples = ranges.reduce((sum, row) => sum + (Date.parse(row.to) - Date.parse(row.from)) / 86400000 + 1, 0);
  return { from: [target.from, ...ranges.map(row => row.from)].filter(Boolean).sort()[0], to: [target.to, ...ranges.map(row => row.to)].filter(Boolean).sort().at(-1)!, bars: target.bars + samples };
}

/** Unknown CDN availability falls back to standard; capability is mock metadata only. */
export function resolveDownloadModes(request: DownloadRequest): Record<string, DownloadMode> {
  return Object.fromEntries(request.targets.map(target => [target.id,
    request.downloadType !== 'standard' && target.fastDownloadAvailable === true ? request.downloadType : 'standard']));
}
export function downloadStep(job: DownloadJob): number {
  const modes = job.resolvedModes ?? resolveDownloadModes(job.request);
  return Math.min(...job.request.targets.map(target => ({ standard: 5, cdn: 10, 'cdn-cn': 8 }[modes[target.id] ?? 'standard'])));
}

/** Expire only this terminal display; a replacement job keeps its own lifecycle. */
export function scheduleFinishedDownloadClear(job: DownloadJob | null, current: () => DownloadJob | null, clear: () => void): () => void {
  if (!job || !['completed', 'failed', 'cancelled'].includes(job.state)) return () => {};
  const timer = setTimeout(() => {
    if (current() === job) clear();
  }, 10_000);
  return () => clearTimeout(timer);
}
