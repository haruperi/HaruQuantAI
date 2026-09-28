/** Owner-local presentation/resource documents; no backend execution authority. */
import { createElement, useEffect } from 'react';
import { DarwinexAddDialog } from './DarwinexAddDialog';
import { DarwinexImportDialog } from './DarwinexImportDialog';
import { DarwinexDownloadDialog } from './DarwinexDownloadDialog';
import { useDarwinex, darwinexActive } from './darwinexStore';
import { darwinexTargets } from './darwinex';

export function validateName(name: string, existing: string[], label = 'Symbol'): void {
  if (!name || name.length > 128 || !/^[a-zA-Z0-9_@.:$]+$/.test(name)) throw new Error(`${label} name is required (maximum 128 characters); use letters, numbers, or _ @ . : $.`);
  if (existing.some(item => item.toLowerCase() === name.toLowerCase())) throw new Error(`${label} ${name} already exists.`);
}

export interface BrokerProfile { id:string;name:string;postfix:string;timezone:string;mtUse:boolean;instruments:string[] }

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

export const pluginId = 'darwinex';
export const pluginName = 'Darwinex';

export function Sync({ onSync }: { onSync: (id: string, state: any) => void }) {
  const state = useDarwinex();
  useEffect(() => {
    const active = darwinexActive(state.job?.state);
    const definitions = [...state.definitions, ...(active && state.job?.kind !== 'download' ? state.job!.definitions.filter(item => !state.definitions.some(row => row.id === item.id)) : [])].map(row => ({
      ...row,
      ...simulationSummary(row, state.ranges[row.id] ?? []),
    }));
    onSync('darwinex', {
      definitions,
      job: state.job,
      ranges: state.ranges,
      storageError: state.storageError,
      active,
    });
  }, [state, onSync]);
  return null;
}

export function Dialogs({ dialog, contextDocument, selectedDatasetIds, onClose, onStarted }: any) {
  if (dialog?.id === 'darwinex-add') {
    return createElement(DarwinexAddDialog, { contextDocument, onClose, onStarted: () => onStarted('darwinex') });
  }
  if (dialog?.id === 'darwinex-import') {
    return createElement(DarwinexImportDialog, { onClose, onStarted: () => onStarted('darwinex') });
  }
  if (dialog?.id === 'darwinex-download') {
    const darwinexState = useDarwinex.getState();
    const targets = darwinexTargets(darwinexState.definitions.filter(row => selectedDatasetIds.includes(row.id))).map(row => ({ ...row, ...simulationSummary(row, darwinexState.ranges[row.id] ?? []) }));
    return createElement(DarwinexDownloadDialog, { targets, onClose, onStarted: () => onStarted('darwinex') });
  }
  return null;
}

export function advance() {
  useDarwinex.getState().advance();
}

export function action(act: 'pause' | 'resume' | 'stop') {
  useDarwinex.getState().action(act);
}

export function onSelectCommand(command: any, context: any) {
  if (command.dialog === 'darwinex-download') {
    try {
      const state = useDarwinex.getState();
      const targets = darwinexTargets(state.definitions.filter(row => context.selectedDatasetIds.includes(row.id)));
      if (!targets.length) throw new Error('You must select at least one Darwinex record.');
      context.setSelectionMessage('');
      context.setDialog({ id: 'darwinex-download' });
    } catch (cause: any) {
      context.setSelectionMessage(cause?.message || 'Unable to select data.');
    }
    return true;
  }
  return false;
}
