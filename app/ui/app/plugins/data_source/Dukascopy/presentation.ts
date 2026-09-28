/** Owner-local presentation/resource documents; no backend execution authority. */
import { createElement, useEffect } from 'react';
import { useHostConnection } from '../../../host/HostConnection';
import { DukascopyAddDialog } from './DukascopyAddDialog';
import { DukascopyDownloadDialog } from './DukascopyDownloadDialog';
import { useDukascopyDownloads } from './dukascopyStore';
import { eligibleTargets } from './dukascopyDownload';

export interface BrokerProfile {
  id: string;
  name: string;
  postfix: string;
  timezone: string;
  mtUse: boolean;
  instruments: string[];
}

export { eligibleTargets };
export const pluginId = 'dukascopy';
export const pluginName = 'Dukascopy';

export function Sync({ onSync }: { onSync: (id: string, state: any) => void }) {
  const state = useDukascopyDownloads();
  const { status } = useHostConnection();
  useEffect(() => {
    if (status === 'online') void useDukascopyDownloads.getState().refresh();
  }, [status]);
  useEffect(() => {
    if (!state.job || !['running', 'paused'].includes(state.job.state)) return;
    const timer = window.setInterval(() => { void useDukascopyDownloads.getState().poll(); }, 1000);
    return () => window.clearInterval(timer);
  }, [state.job?.state]);
  useEffect(() => {
    const active = state.job?.state === 'running' || state.job?.state === 'paused';
    onSync('dukascopy', {
      job: state.job,
      ranges: state.ranges,
      storageError: state.storageError,
      active,
      definitions: state.definitions,
      backendAvailable: state.definitionsAvailable,
      reason: state.reason,
    });
  }, [state, onSync]);
  return null;
}

export function Dialogs({ dialog, contextDocument, selectedDatasetIds, toolRows, onClose, onStarted, onComplete }: any) {
  const state = useDukascopyDownloads();
  if (dialog?.id === 'dukascopy-add') {
    return createElement(DukascopyAddDialog, {
      open: true,
      contextDocument: {
        ...contextDocument,
        brokers: state.brokers,
        brokerCatalogStatus: state.brokerCatalogStatus,
      },
      onClose, onComplete,
      available: state.definitionsAvailable,
      onAddData: state.addData,
    });
  }
  if (dialog?.id === 'dukascopy-download') {
    const selected = (toolRows ?? []).filter((row: any) => selectedDatasetIds.includes(row.id));
    const eligible = eligibleTargets(selected, state.job);
    return createElement(DukascopyDownloadDialog, { targets: eligible, onClose, onStarted: () => onStarted('download', 'Dukascopy download submitted') });
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
