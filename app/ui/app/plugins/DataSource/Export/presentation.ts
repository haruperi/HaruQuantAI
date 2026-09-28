/** Owner-local presentation/resource documents; no backend execution authority. */
import { createElement, useEffect } from 'react';
import { CsvExportDialog } from './CsvExportDialog';
import { Mt4ExportDialog } from './Mt4ExportDialog';
import { Mt5ExportDialog } from './Mt5ExportDialog';
import { useDataExports, exportActive } from './dataExportStore';
import { downloadExportArtifacts, selectExportTargets, type ExportKind, type ExportTarget } from './dataExport';

export type Preset = 'sinceLast' | 'sixMonths' | 'year' | 'fiveYears' | 'tenYears' | 'allTime' | 'custom';

export function presetRange(preset: Preset, last: string, minimum: string, from: string, to: string, now = today()): Interval {
  if (preset === 'custom') return { from, to };
  if (preset === 'allTime') return { from: minimum, to: now };
  if (preset === 'sinceLast') return { from: last, to };
  const date = new Date(`${now}T12:00:00Z`);
  if (preset === 'sixMonths') date.setUTCMonth(date.getUTCMonth() - 6);
  else date.setUTCFullYear(date.getUTCFullYear() - ({ year: 1, fiveYears: 5, tenYears: 10 }[preset]));
  return { from: [minimum, date.toISOString().slice(0, 10)].sort().at(-1)!, to };
}

export function today(): string { const now = new Date(); return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`; }

export interface Interval { from: string; to: string }

export function validDate(value: string): boolean { return /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value; }

export { selectExportTargets, downloadExportArtifacts, exportActive };
export type { ExportKind, ExportTarget };

export const pluginId = 'export';
export const pluginName = 'Export';

export function Sync({ onSync }: { onSync: (id: string, state: any) => void }) {
  const state = useDataExports();
  useEffect(() => {
    const active = exportActive(state.job?.state);
    onSync('export', {
      job: state.job,
      formats: state.formats,
      settings: state.settings,
      storageError: state.storageError,
      active,
    });
  }, [state, onSync]);
  return null;
}

export function Dialogs({ exportDialog, externalActive, onClose, onStarted }: any) {
  if (!exportDialog) return null;
  if (exportDialog.kind === 'csv') {
    return createElement(CsvExportDialog, { targets: exportDialog.targets, externalActive, onClose, onStarted: () => onStarted('export', 'CSV export started (simulation)') });
  }
  if (exportDialog.kind === 'mt4') {
    return createElement(Mt4ExportDialog, { target: exportDialog.targets[0], externalActive, onClose, onStarted: () => onStarted('export', 'MT4 mock export started') });
  }
  if (exportDialog.kind === 'mt5') {
    return createElement(Mt5ExportDialog, { target: exportDialog.targets[0], externalActive, onClose, onStarted: () => onStarted('export', 'MT5 export started (simulation)') });
  }
  return null;
}

export function advance() {
  useDataExports.getState().advance();
}

export function action(act: 'pause' | 'resume' | 'stop') {
  useDataExports.getState().action(act);
}
