/** Owner-local presentation/resource documents; no backend execution authority. */
import { createElement, useEffect } from 'react';
import { YahooAddDialog } from './YahooAddDialog';
import { YahooDownloadDialog } from './YahooDownloadDialog';
import { useYahoo, yahooActive } from './yahooStore';
import { yahooTargets } from './yahoo';

export function today(): string { const now = new Date(); return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`; }

export function validDate(value: string): boolean { return /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value; }

export interface Interval { from: string; to: string }

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

export function presetRange(preset: Preset, last: string, minimum: string, from: string, to: string, now = today()): Interval {
  if (preset === 'custom') return { from, to };
  if (preset === 'allTime') return { from: minimum, to: now };
  if (preset === 'sinceLast') return { from: last, to };
  const date = new Date(`${now}T12:00:00Z`);
  if (preset === 'sixMonths') date.setUTCMonth(date.getUTCMonth() - 6);
  else date.setUTCFullYear(date.getUTCFullYear() - ({ year: 1, fiveYears: 5, tenYears: 10 }[preset]));
  return { from: [minimum, date.toISOString().slice(0, 10)].sort().at(-1)!, to };
}

export function simulationSummary(target: { from?: string; to?: string; bars?: number }, ranges: Interval[]) {
  const from = target.from ?? '';
  const to = target.to ?? '';
  const bars = target.bars ?? 0;
  if (!ranges.length) return { from, to, bars };
  const samples = ranges.reduce((sum, row) => sum + (Date.parse(row.to) - Date.parse(row.from)) / 86400000 + 1, 0);
  return { from: [from, ...ranges.map(row => row.from)].filter(Boolean).sort()[0], to: [to, ...ranges.map(row => row.to)].filter(Boolean).sort().at(-1)!, bars: bars + samples };
}

export const pluginId = 'yahoo';
export const pluginName = 'Yahoo';

export function Sync({ onSync }: { onSync: (id: string, state: any) => void }) {
  const state = useYahoo();
  useEffect(() => { void useYahoo.getState().refresh(); }, []);
  useEffect(() => {
    if (!yahooActive(state.job?.state)) return;
    const timer = setInterval(() => { void useYahoo.getState().poll(); }, 1000);
    return () => clearInterval(timer);
  }, [state.job?.state]);
  useEffect(() => {
    const active = yahooActive(state.job?.state);
    onSync('yahoo', {
      definitions: state.definitions,
      backendAvailable: state.backendAvailable,
      job: state.job,
      ranges: state.ranges,
      storageError: state.storageError,
      active,
    });
  }, [state, onSync]);
  return null;
}

export function Dialogs({ dialog, contextDocument, selectedDatasetIds, onClose, onStarted }: any) {
  if (dialog?.id === 'yahoo-add') {
    return createElement(YahooAddDialog, { contextDocument, onClose, onStarted: () => onStarted('yahoo', 'Yahoo symbols added') });
  }
  if (dialog?.id === 'yahoo-download') {
    const yahooState = useYahoo.getState();
    const targets = yahooTargets(yahooState.definitions.filter(row => selectedDatasetIds.includes(row.id)));
    return createElement(YahooDownloadDialog, { contextDocument, targets, onClose, onStarted: () => onStarted('yahoo', 'Yahoo download submitted') });
  }
  return null;
}

export function advance() {
  useYahoo.getState().advance();
}

export function action(act: 'pause' | 'resume' | 'stop') {
  useYahoo.getState().action(act);
}

export function onSelectCommand(command: any, context: any) {
  if (command.dialog === 'yahoo-download') {
    try {
      const state = useYahoo.getState();
      const targets = yahooTargets(state.definitions.filter(row => context.selectedDatasetIds.includes(row.id)));
      if (!targets.length) throw new Error('You must select at least one Yahoo record.');
      context.setSelectionMessage('');
      context.setDialog({ id: 'yahoo-download' });
    } catch (cause: any) {
      context.setSelectionMessage(cause?.message || 'Unable to select Yahoo data.');
    }
    return true;
  }
  return false;
}
