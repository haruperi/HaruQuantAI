/** Owner-local presentation/resource documents; no backend execution authority. */
import { createElement, useEffect } from 'react';
import { Mt5ImportDialog } from './Mt5ImportDialog';
import { useMt5Import, mt5Active } from './mt5ImportStore';
import { mt5Summary } from './mt5Import';

export function today(): string { const now = new Date(); return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`; }

export type Preset = 'sinceLast' | 'sixMonths' | 'year' | 'fiveYears' | 'tenYears' | 'allTime' | 'custom';

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

export interface Interval { from: string; to: string }

export function validDate(value: string): boolean { return /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value; }

export function presetRange(preset: Preset, last: string, minimum: string, from: string, to: string, now = today()): Interval {
  if (preset === 'custom') return { from, to };
  if (preset === 'allTime') return { from: minimum, to: now };
  if (preset === 'sinceLast') return { from: last, to };
  const date = new Date(`${now}T12:00:00Z`);
  if (preset === 'sixMonths') date.setUTCMonth(date.getUTCMonth() - 6);
  else date.setUTCFullYear(date.getUTCFullYear() - ({ year: 1, fiveYears: 5, tenYears: 10 }[preset]));
  return { from: [minimum, date.toISOString().slice(0, 10)].sort().at(-1)!, to };
}

export function simulationSummary(target: DownloadTarget, ranges: Interval[]) {
  if (!ranges.length) return { from: target.from, to: target.to, bars: target.bars };
  const samples = ranges.reduce((sum, row) => sum + (Date.parse(row.to) - Date.parse(row.from)) / 86400000 + 1, 0);
  return { from: [target.from, ...ranges.map(row => row.from)].filter(Boolean).sort()[0], to: [target.to, ...ranges.map(row => row.to)].filter(Boolean).sort().at(-1)!, bars: target.bars + samples };
}

export interface DownloadTarget { id: string; symbol: string; source: string; underlying?: string; instrument?: string; timeframe: string; from: string; to: string; bars: number; sourceDataId?: string; fastDownloadAvailable?: boolean }

export interface BrokerProfile { id: string; name: string; postfix: string; timezone: string; mtUse: boolean; instruments: string[] }

export const pluginId = 'mt5';
export const pluginName = 'MT5';

export function Sync({ onSync }: { onSync: (id: string, state: any) => void }) {
  const state = useMt5Import();
  useEffect(() => {
    const active = mt5Active(state.job?.state);
    const definitions = [...state.definitions, ...(active ? state.job!.definitions.filter(item => !state.definitions.some(row => row.id === item.id)) : [])].map(row => ({
      ...row,
      ...mt5Summary(row, state.ranges[row.id] ?? []),
    }));
    onSync('mt5', {
      definitions,
      job: state.job,
      ranges: state.ranges,
      storageError: state.storageError,
      active,
    });
  }, [state, onSync]);
  return null;
}

export function Dialogs({ dialog, contextDocument, onClose, onStarted }: any) {
  if (dialog?.id === 'mt5-import') {
    return createElement(Mt5ImportDialog, { contextDocument, onClose, onStarted: () => onStarted('mt5', 'MT5 import started (simulation)') });
  }
  return null;
}

export function advance() {
  useMt5Import.getState().advance();
}

export function action(act: 'pause' | 'resume' | 'stop') {
  useMt5Import.getState().action(act);
}
