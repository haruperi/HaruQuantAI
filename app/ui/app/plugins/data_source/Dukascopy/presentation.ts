/** Owner-local presentation/resource documents; no backend execution authority. */
import { createElement, useEffect } from 'react';
import { DukascopyAddDialog } from './DukascopyAddDialog';
import { DukascopyDownloadDialog } from './DukascopyDownloadDialog';
import { useDukascopyDownloads } from './dukascopyStore';
import { eligibleTargets, simulationSummary } from './dukascopyDownload';

export interface BrokerProfile {
  id: string;
  name: string;
  postfix: string;
  timezone: string;
  mtUse: boolean;
  instruments: string[];
}

export { simulationSummary, eligibleTargets };
export const pluginId = 'dukascopy';
export const pluginName = 'Dukascopy';

export function Sync({ onSync }: { onSync: (id: string, state: any) => void }) {
  const state = useDukascopyDownloads();
  useEffect(() => {
    const active = state.job?.state === 'running' || state.job?.state === 'paused';
    onSync('dukascopy', {
      job: state.job,
      ranges: state.ranges,
      storageError: state.storageError,
      active,
    });
  }, [state, onSync]);
  return null;
}

export function Dialogs({ dialog, contextDocument, selectedDatasetIds, toolRows, onClose, onStarted, onComplete, onAddData }: any) {
  if (dialog?.id === 'dukascopy-add') {
    return createElement(DukascopyAddDialog, { open: true, contextDocument, onClose, onAddData, onComplete });
  }
  if (dialog?.id === 'dukascopy-download') {
    const state = useDukascopyDownloads.getState();
    const selected = (toolRows ?? []).filter((row: any) => selectedDatasetIds.includes(row.id));
    const eligible = eligibleTargets(selected, state.job).map(row => ({ ...row, ...simulationSummary(row, state.ranges[row.id] ?? []) }));
    return createElement(DukascopyDownloadDialog, { targets: eligible, onClose, onStarted: () => onStarted('download', 'Dukascopy download started (simulation)') });
  }
  return null;
}

export function advance() {
  useDukascopyDownloads.getState().advance();
}

export function action(act: 'pause' | 'resume' | 'stop') {
  useDukascopyDownloads.getState().action(act);
}

export function onSelectCommand(command: any, context: any) {
  if (command.dialog === 'dukascopy-download') {
    try {
      const state = useDukascopyDownloads.getState();
      const selected = (context.datasets ?? []).filter((row: any) => context.selectedDatasetIds.includes(row.id));
      eligibleTargets(selected, state.job);
      context.setSelectionMessage('');
      context.setDialog({ id: 'dukascopy-download' });
    } catch (cause: any) {
      context.setSelectionMessage(cause?.message || 'Unable to select data');
    }
    return true;
  }
  return false;
}
