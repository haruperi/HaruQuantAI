export type ToolJobState = 'running' | 'paused' | 'cancelled' | 'completed' | 'failed';

export interface ToolTarget {
  id: string; symbol: string; instrument: string; source: string; timeframe: string;
  timezone: string; from: string; to: string; bars: number; category: string;
  brokerName?: string; underlying?: string; barType?: string; sourceDataId?: string;
}

export interface CloneSettings {
  postfix: string;
  timezoneType: 'shift' | 'zone';
  shiftHours: number;
  timezone: string;
  removeWeekends: boolean;
}

export interface CloneDefinition extends ToolTarget {
  sourceDataId: string;
  sourceSymbol: string;
  cloneSettings: CloneSettings;
  quality: number;
  status: 'Ready';
}

export interface ReviewRow {
  id: string; date: string; open: number; high: number; low: number; close: number;
  volume: number; bid: number; ask: number;
}

export interface ReviewMutation { changed: Record<string, Partial<ReviewRow>>; deleted: string[] }
export interface QualityIssue { id: string; date: string; kind: 'Gap' | 'Spike' | 'Bad OHLC'; row: ReviewRow }
export interface QualityResult {
  counts: { gap: number; spike: number; ohlc: number };
  percents: { gap: string; spike: string; ohlc: string };
  issues: QualityIssue[];
  distribution: { bucket: string; gaps: number; spikes: number; ohlc: number }[];
}

export const toolTimezones = [
  'UTC', 'Europe/London', 'Europe/Prague', 'America/New_York', 'America/Chicago',
  'Asia/Tokyo', 'Asia/Hong_Kong', 'Australia/Sydney',
] as const;
export const toolSessions = ['No Session', 'Forex 24/5', 'CME Equity', 'US stocks', 'Metals'] as const;
export const reviewTimeframes = ['TICK', 'M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1', 'MN1'] as const;

const frameMinutes: Record<string, number> = { TICK: 0, M1: 1, M5: 5, M15: 15, M30: 30, H1: 60, H4: 240, D1: 1440, W1: 10080, MN1: 40320 };

function importedFrame(value: string): string {
  const raw = value.split(/\s*(?:→|-)\s*/)[0]?.trim().toUpperCase() || 'M1';
  if (raw === 'TICK' || raw === 'INTRADAY') return raw;
  return Object.hasOwn(frameMinutes, raw) ? raw : 'M1';
}

export function availableReviewTimeframes(value: string): string[] {
  const imported = importedFrame(value);
  if (imported === 'INTRADAY') return ['INTRADAY'];
  const minimum = frameMinutes[imported] ?? 1;
  return reviewTimeframes.filter(item => frameMinutes[item] >= minimum);
}

export function selectCloneTargets(rows: ToolTarget[], ids: string[]): ToolTarget[] {
  const selected = rows.filter(row => ids.includes(row.id));
  if (!selected.length) throw new Error('You have to select some symbol.');
  const cloned = selected.find(row => row.sourceDataId);
  if (cloned) throw new Error(`'${cloned.symbol}' is cloned data. You cannot clone it again.`);
  return selected;
}

export function selectReviewTarget(rows: ToolTarget[], ids: string[]): ToolTarget {
  const selected = rows.filter(row => ids.includes(row.id));
  if (!selected.length) throw new Error('You have to select a symbol.');
  const target = selected[0];
  if (!target.bars) throw new Error(`Symbol '${target.symbol}' doesn't contain any data`);
  return target;
}

function safePart(value: string): string {
  return value.trim().replace(/[^A-Za-z0-9_+.-]+/g, '_').replace(/^_+|_+$/g, '');
}

export function cloneTimeLabel(settings: CloneSettings): string {
  if (settings.timezoneType === 'shift') return settings.shiftHours >= 0 ? `+${settings.shiftHours}` : String(settings.shiftHours);
  return settings.timezone.split('/').at(-1)?.replace(/_/g, '-') || 'UTC';
}

export function cloneSymbol(target: ToolTarget, settings: CloneSettings, used: Set<string>): string {
  const postfix = settings.postfix.replaceAll('{timeframe}', importedFrame(target.timeframe))
    .replaceAll('{cloneTime}', cloneTimeLabel(settings));
  if (!postfix.trim()) throw new Error('Symbol postfix cannot be empty.');
  const base = safePart(`${target.symbol}${postfix}`);
  if (!base || base.length > 120) throw new Error('The generated symbol name is invalid or too long.');
  let candidate = base; let suffix = 2;
  while (used.has(candidate.toLowerCase())) candidate = `${base}_${suffix++}`;
  used.add(candidate.toLowerCase());
  return candidate;
}

export function validateCloneSettings(settings: CloneSettings): void {
  if (!settings.postfix.trim() || settings.postfix.length > 80) throw new Error('Symbol postfix cannot be empty and must be at most 80 characters.');
  if (!Number.isInteger(settings.shiftHours) || settings.shiftHours < -23 || settings.shiftHours > 23) throw new Error('Timezone shift must be a whole number from -23 to 23.');
  if (settings.timezoneType === 'zone' && !toolTimezones.includes(settings.timezone as typeof toolTimezones[number])) throw new Error('Choose a supported timezone.');
}

export function createCloneDefinitions(targets: ToolTarget[], settings: CloneSettings, existingNames: string[]): CloneDefinition[] {
  validateCloneSettings(settings);
  const used = new Set(existingNames.map(name => name.toLowerCase()));
  return targets.map(target => {
    const symbol = cloneSymbol(target, settings, used);
    const timezone = settings.timezoneType === 'zone' ? settings.timezone
      : `${target.timezone && target.timezone !== '—' ? target.timezone : 'UTC'} ${settings.shiftHours >= 0 ? '+' : ''}${settings.shiftHours}h`;
    return { ...target, id: `clone:${target.id}:${symbol}`, symbol, instrument: symbol,
      underlying: target.underlying || target.symbol, timezone, source: 'Cloned data', sourceDataId: target.id,
      sourceSymbol: target.symbol, cloneSettings: { ...settings }, quality: 100, status: 'Ready' };
  });
}

function hash(value: string): number {
  let result = 2166136261;
  for (const char of value) { result ^= char.charCodeAt(0); result = Math.imul(result, 16777619); }
  return result >>> 0;
}
function decimal(value: number): number { return Number(value.toFixed(value < 10 ? 5 : 2)); }
function intervalMs(frame: string): number { return Math.max(1, frameMinutes[frame] ?? 1) * 60000; }

export function reviewKey(targetId: string, timeframe: string, session: string): string { return `${targetId}|${timeframe}|${session}`; }

export function generateReviewRows(target: ToolTarget, timeframe: string, session: string, count = 480): ReviewRow[] {
  const bounded = Math.max(1, Math.min(1000, count));
  const seed = hash(`${target.id}|${timeframe}|${session}`); const tick = timeframe === 'TICK';
  const start = Number.isFinite(Date.parse(`${target.from}T00:00:00Z`)) ? Date.parse(`${target.from}T00:00:00Z`) : Date.UTC(2024, 0, 1);
  const step = tick ? 1000 : intervalMs(timeframe); const base = target.category === 'Forex' ? 1 + (seed % 70) / 100 : 50 + seed % 1500;
  return Array.from({ length: bounded }, (_, index) => {
    const accumulatedGap = Math.floor(index / 137) * step * 3;
    const time = start + index * step + accumulatedGap; const wave = Math.sin((index + seed % 97) / 17) * base * .003;
    const open = base + wave; const close = open + Math.cos((index + seed % 31) / 11) * base * .0008;
    const spike = index > 0 && index % 211 === 0 ? base * .025 : 0;
    const adjustedClose = close + spike; const spread = Math.max(base * .00008, .00001);
    let high = Math.max(open, adjustedClose) + base * .0006; let low = Math.min(open, adjustedClose) - base * .0006;
    if (index > 0 && index % 307 === 0) high = Math.min(open, adjustedClose) - spread;
    return { id: new Date(time).toISOString(), date: new Date(time).toISOString(), open: decimal(open), high: decimal(high),
      low: decimal(low), close: decimal(adjustedClose), bid: decimal(adjustedClose - spread / 2), ask: decimal(adjustedClose + spread / 2),
      volume: 100 + (seed * (index + 3)) % 900 };
  });
}

export function applyReviewMutation(rows: ReviewRow[], mutation?: ReviewMutation): ReviewRow[] {
  if (!mutation) return rows;
  const deleted = new Set(mutation.deleted);
  return rows.filter(row => !deleted.has(row.id)).map(row => ({ ...row, ...(mutation.changed[row.id] ?? {}) }));
}

export function validateReviewChange(row: ReviewRow, tick: boolean): void {
  const values = tick ? [row.bid, row.ask, row.volume] : [row.open, row.high, row.low, row.close, row.volume];
  if (values.some(value => !Number.isFinite(value))) throw new Error('Edited values must be valid numbers.');
  if (row.volume < 0) throw new Error('Volume cannot be negative.');
  if (tick && row.ask < row.bid) throw new Error('Ask cannot be lower than Bid.');
}

export function analyzeQuality(rows: ReviewRow[], timeframe: string): QualityResult {
  const issues: QualityIssue[] = []; const expected = intervalMs(timeframe);
  rows.forEach((row, index) => {
    if (index && Date.parse(row.date) - Date.parse(rows[index - 1].date) > expected * 1.5) issues.push({ id: `gap:${row.id}`, date: row.date, kind: 'Gap', row });
    if (index) { const prior = rows[index - 1].close; if (Math.abs(row.close - prior) / Math.max(Math.abs(prior), .00001) > .015) issues.push({ id: `spike:${row.id}`, date: row.date, kind: 'Spike', row }); }
    if (row.high < Math.max(row.open, row.close) || row.low > Math.min(row.open, row.close) || row.low > row.high) issues.push({ id: `ohlc:${row.id}`, date: row.date, kind: 'Bad OHLC', row });
  });
  const gap = issues.filter(item => item.kind === 'Gap').length; const spike = issues.filter(item => item.kind === 'Spike').length; const ohlc = issues.filter(item => item.kind === 'Bad OHLC').length;
  const percent = (value: number) => `${(value / Math.max(rows.length, 1) * 100).toFixed(2)}%`;
  const buckets = new Map<string, { gaps: number; spikes: number; ohlc: number }>();
  for (const issue of issues) { const bucket = issue.date.slice(0, 7); const item = buckets.get(bucket) ?? { gaps: 0, spikes: 0, ohlc: 0 }; if (issue.kind === 'Gap') item.gaps++; else if (issue.kind === 'Spike') item.spikes++; else item.ohlc++; buckets.set(bucket, item); }
  return { counts: { gap, spike, ohlc }, percents: { gap: percent(gap), spike: percent(spike), ohlc: percent(ohlc) }, issues,
    distribution: [...buckets].map(([bucket, values]) => ({ bucket, ...values })) };
}
